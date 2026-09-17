import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.models import HairAssessment
from app.modules.recommendation.models import UserRoutine, RulesConfig, ProtocolConfig
from app.modules.recommendation.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    AdminRoutineUpdate,
    AdminRuleResponse,
    AdminRuleUpdate,
    AdminProtocolResponse,
    AdminProtocolUpdate,
    Phase,
    PhaseAction,
)
from app.modules.recommendation.engine import run_engine
from app.modules.recommendation.escalation import evaluate_escalation

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])



@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendation(
    payload: RecommendationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.tier == "RED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Escalation precondition: assessment tier is RED. Recommendation engine cannot be invoked.",
        )

    user_uuid = uuid.UUID(current_user.uid)
    assessment = (
        db.query(HairAssessment)
        .filter(HairAssessment.user_id == user_uuid)
        .first()
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hair ID assessment must be completed before generating recommendations.",
        )

    results = assessment.results or {}
    if assessment.status == "escalated" or results.get("tier") == "RED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Escalation precondition: assessment tier is RED. Recommendation engine cannot be invoked.",
        )

    if assessment.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hair ID assessment must be completed before generating recommendations.",
        )

    escalation_res = evaluate_escalation(assessment.answers or {}, db=db)
    if escalation_res.requires_escalation or escalation_res.tier == "RED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Escalation precondition: assessment answers triggered RED tier. Recommendation engine cannot be invoked.",
        )

    result = run_engine(assessment.answers, payload.concern, db)

    roadmap = [
        Phase(
            phase=p["phase"],
            name=p["name"],
            days=p["days"],
            actions=[PhaseAction.model_validate(a) for a in p.get("actions", [])],
            checkpoint_day=p.get("checkpoint_day"),
            checkpoint_metric=p.get("checkpoint_metric"),
        )
        for p in result["roadmap"]
    ]

    roadmap_dicts = [p.model_dump(by_alias=True) for p in roadmap]

    routine = db.query(UserRoutine).filter(UserRoutine.user_id == user_uuid).first()
    if routine is None:
        routine = UserRoutine(
            user_id=user_uuid,
            assessment_id=assessment.id,
            active_problems=result["active_problems"],
            cause_explanation_keys=result["cause_explanation_keys"],
            protocols=result["protocols"],
            roadmap=roadmap_dicts,
            product_weight_ceiling=result["product_weight_ceiling"],
            hard_guards_fired=result["hard_guards_fired"],
            realistic_timeline_weeks=result["realistic_timeline_weeks"],
            is_customized=False,
            admin_notes=None,
        )
        db.add(routine)
    else:
        routine.assessment_id = assessment.id
        routine.active_problems = result["active_problems"]
        routine.cause_explanation_keys = result["cause_explanation_keys"]
        routine.protocols = result["protocols"]
        routine.roadmap = roadmap_dicts
        routine.product_weight_ceiling = result["product_weight_ceiling"]
        routine.hard_guards_fired = result["hard_guards_fired"]
        routine.realistic_timeline_weeks = result["realistic_timeline_weeks"]
        routine.is_customized = False
        routine.admin_notes = None

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        routine = db.query(UserRoutine).filter(UserRoutine.user_id == user_uuid).first()
        if routine is not None:
            routine.assessment_id = assessment.id
            routine.active_problems = result["active_problems"]
            routine.cause_explanation_keys = result["cause_explanation_keys"]
            routine.protocols = result["protocols"]
            routine.roadmap = roadmap_dicts
            routine.product_weight_ceiling = result["product_weight_ceiling"]
            routine.hard_guards_fired = result["hard_guards_fired"]
            routine.realistic_timeline_weeks = result["realistic_timeline_weeks"]
            routine.is_customized = False
            routine.admin_notes = None
            db.commit()
    db.refresh(routine)

    return RecommendationResponse(
        user_id=str(routine.user_id),
        active_problems=routine.active_problems,
        cause_explanation_keys=routine.cause_explanation_keys,
        protocols=routine.protocols,
        roadmap=[Phase.model_validate(p) for p in routine.roadmap],
        product_weight_ceiling=routine.product_weight_ceiling,
        hard_guards_fired=routine.hard_guards_fired,
        realistic_timeline_weeks=routine.realistic_timeline_weeks,
        is_customized=routine.is_customized,
        admin_notes=routine.admin_notes,
    )


@router.get("/me", response_model=RecommendationResponse)
def get_my_routine(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_uuid = uuid.UUID(current_user.uid)
    routine = db.query(UserRoutine).filter(UserRoutine.user_id == user_uuid).first()
    if routine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active routine found for this user.",
        )

    return RecommendationResponse(
        user_id=str(routine.user_id),
        active_problems=routine.active_problems,
        cause_explanation_keys=routine.cause_explanation_keys,
        protocols=routine.protocols,
        roadmap=[Phase.model_validate(p) for p in routine.roadmap],
        product_weight_ceiling=routine.product_weight_ceiling,
        hard_guards_fired=routine.hard_guards_fired,
        realistic_timeline_weeks=routine.realistic_timeline_weeks,
        is_customized=routine.is_customized,
        admin_notes=routine.admin_notes,
    )


@router.patch("/admin/users/{user_id}", response_model=RecommendationResponse)
def admin_update_user_routine(
    user_id: str,
    payload: AdminRoutineUpdate,
    admin_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db),
):

    try:
        target_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user UUID format.",
        )

    routine = db.query(UserRoutine).filter(UserRoutine.user_id == target_uuid).first()
    if routine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User routine not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    if "roadmap" in update_data and payload.roadmap is not None:
        routine.roadmap = [p.model_dump(by_alias=True) for p in payload.roadmap]
    if "admin_notes" in update_data:
        routine.admin_notes = payload.admin_notes
    if "product_weight_ceiling" in update_data and payload.product_weight_ceiling is not None:
        routine.product_weight_ceiling = payload.product_weight_ceiling

    routine.is_customized = True
    db.commit()
    db.refresh(routine)

    return RecommendationResponse(
        user_id=str(routine.user_id),
        active_problems=routine.active_problems,
        cause_explanation_keys=routine.cause_explanation_keys,
        protocols=routine.protocols,
        roadmap=[Phase.model_validate(p) for p in routine.roadmap],
        product_weight_ceiling=routine.product_weight_ceiling,
        hard_guards_fired=routine.hard_guards_fired,
        realistic_timeline_weeks=routine.realistic_timeline_weeks,
        is_customized=routine.is_customized,
        admin_notes=routine.admin_notes,
    )


@router.get("/admin/rules", response_model=list[AdminRuleResponse])
def admin_list_rules(
    admin_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rules = db.query(RulesConfig).order_by(RulesConfig.priority.asc()).all()
    return [
        AdminRuleResponse(
            problem_id=r.problem_id,
            display_name=r.display_name,
            priority=r.priority,
            is_active=r.is_active,
            protocol_id=r.protocol_id,
            classifier=r.classifier or {},
            score_boosters=r.score_boosters or [],
            hard_guards=r.hard_guards or [],
            realistic_timeline_weeks=r.realistic_timeline_weeks or {},
            root_cause_explanation_key=r.root_cause_explanation_key,
            always_runs_as_module=r.always_runs_as_module,
        )
        for r in rules
    ]


@router.patch("/admin/rules/{problem_id}", response_model=AdminRuleResponse)
def admin_update_rule(
    problem_id: str,
    payload: AdminRuleUpdate,
    admin_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule = db.query(RulesConfig).filter(RulesConfig.problem_id == problem_id).first()
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    for field, val in update_data.items():
        setattr(rule, field, val)

    db.commit()
    db.refresh(rule)

    return AdminRuleResponse(
        problem_id=rule.problem_id,
        display_name=rule.display_name,
        priority=rule.priority,
        is_active=rule.is_active,
        protocol_id=rule.protocol_id,
        classifier=rule.classifier or {},
        score_boosters=rule.score_boosters or [],
        hard_guards=rule.hard_guards or [],
        realistic_timeline_weeks=rule.realistic_timeline_weeks or {},
        root_cause_explanation_key=rule.root_cause_explanation_key,
        always_runs_as_module=rule.always_runs_as_module,
    )


@router.get("/admin/protocols", response_model=list[AdminProtocolResponse])
def admin_list_protocols(
    admin_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db),
):
    protocols = db.query(ProtocolConfig).order_by(ProtocolConfig.id.asc()).all()
    return [
        AdminProtocolResponse(
            id=p.id,
            name=p.name,
            problem_id=p.problem_id,
            phases=p.phases or [],
            is_active=p.is_active,
        )
        for p in protocols
    ]


@router.patch("/admin/protocols/{protocol_id}", response_model=AdminProtocolResponse)
def admin_update_protocol(
    protocol_id: str,
    payload: AdminProtocolUpdate,
    admin_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db),
):
    protocol = db.query(ProtocolConfig).filter(ProtocolConfig.id == protocol_id).first()
    if protocol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    for field, val in update_data.items():
        setattr(protocol, field, val)

    db.commit()
    db.refresh(protocol)

    return AdminProtocolResponse(
        id=protocol.id,
        name=protocol.name,
        problem_id=protocol.problem_id,
        phases=protocol.phases or [],
        is_active=protocol.is_active,
    )


