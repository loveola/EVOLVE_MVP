from typing import Sequence, Union
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "006_create_escalation_flags"
down_revision: Union[str, None] = "005_create_protocols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_FLAGS = [
  {
    "flag_code": "RED_01_SCARRING_CENTRAL",
    "description": "Central/vertex scarring alopecia pattern",
    "trigger_reason": "CCCA begins at the vertex/crown and spreads centrifugally. Loss of follicular ostia (visibly smooth, poreless scalp) indicates follicular destruction that is permanent. Central hair breakage at the crown is a recognised presenting sign (forme fruste CCCA) and is routinely mistaken for a haircare problem. Prevalence approx 2.7-5.7% in women of African descent; mean age at presentation approx 36. Early anti-inflammatory treatment can halt progression; delay cannot be undone.",
    "tier": "RED",
    "conditions": {
      "any_of": [
        {
          "all_of": [
            {
              "field": "h2_loss_location",
              "contains": "crown_vertex"
            },
            {
              "field": "h3_smooth_shiny_no_visible_pores",
              "equals": "yes"
            }
          ]
        },
        {
          "all_of": [
            {
              "field": "h2_loss_location",
              "contains": "crown_vertex"
            },
            {
              "field": "g4_concern_duration",
              "in": [
                "3_12m",
                "gt_12m"
              ]
            },
            {
              "field": "h4_scalp_symptoms",
              "contains_any": [
                "tenderness",
                "tingling_crawling",
                "burning",
                "persistent_itch"
              ]
            }
          ]
        },
        {
          "all_of": [
            {
              "field": "g1_primary_concern",
              "contains": "breakage"
            },
            {
              "field": "h2_loss_location",
              "contains": "crown_vertex"
            },
            {
              "field": "h2_loss_location",
              "not_contains": "all_over"
            }
          ]
        },
        {
          "all_of": [
            {
              "field": "h2_loss_location",
              "contains": "crown_vertex"
            },
            {
              "field": "h5_scalp_lesions",
              "contains_any": [
                "thick_scaly_plaques",
                "pustules_pus_bumps"
              ]
            }
          ]
        }
      ]
    },
    "metadata": {
      "priority": 1,
      "user_message_key": "esc.red.central_scarring",
      "referral_urgency": "within_4_weeks",
      "referral_specialty": "dermatology",
      "referral_note_template": "central_scarring_summary"
    },
    "active": True
  },
  {
    "flag_code": "RED_02_TRACTION_ADVANCED",
    "description": "Traction alopecia with inflammatory or scarring signs",
    "trigger_reason": "Traction alopecia is biphasic: reversible early, scarring late. Affects up to roughly one third of women of African descent. Perifollicular erythema, pustules (traction folliculitis) and broken hairs mark the active phase; follicular scarring and permanent loss follow. Loss of visible follicular openings at the margin means the window has closed. The fringe sign (retained short fine hairs at the very edge) is present in around 90% of cases and is a marker, not a reassurance.",
    "tier": "RED",
    "conditions": {
      "all_of": [
        {
          "field": "h2_loss_location",
          "contains_any": [
            "hairline_temples",
            "nape"
          ]
        },
        {
          "any_of": [
            {
              "field": "h4_scalp_symptoms",
              "contains": "pain_after_styling"
            },
            {
              "field": "h5_scalp_lesions",
              "contains_any": [
                "pustules_pus_bumps",
                "open_sores_scabs"
              ]
            },
            {
              "field": "h3_smooth_shiny_no_visible_pores",
              "equals": "yes"
            },
            {
              "all_of": [
                {
                  "field": "g6_style_tension_pain",
                  "equals": "often"
                },
                {
                  "field": "g4_concern_duration",
                  "in": [
                    "3_12m",
                    "gt_12m"
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    "metadata": {
      "priority": 2,
      "user_message_key": "esc.red.traction_advanced",
      "referral_urgency": "within_4_weeks",
      "referral_specialty": "dermatology",
      "referral_note_template": "traction_summary"
    },
    "active": True
  },
  {
    "flag_code": "RED_03_PATCHY_SMOOTH_SUDDEN",
    "description": "Sudden well-defined smooth patches",
    "trigger_reason": "Round or oval patches that are completely smooth, without scale, inflammation or broken hairs, appearing over days to weeks, with possible eyebrow, eyelash or body hair involvement and nail pitting. Requires medical diagnosis and immunomodulatory management.",
    "tier": "RED",
    "conditions": {
      "any_of": [
        {
          "all_of": [
            {
              "field": "h6_smooth_round_patches_recent_onset",
              "equals": "yes"
            },
            {
              "field": "h5_scalp_lesions",
              "not_contains_any": [
                "black_dots",
                "thick_scaly_plaques"
              ]
            }
          ]
        },
        {
          "all_of": [
            {
              "field": "h6_smooth_round_patches_recent_onset",
              "equals": "yes"
            },
            {
              "field": "h7_eyebrow_eyelash_or_body_hair_loss",
              "equals": "yes"
            }
          ]
        }
      ]
    },
    "metadata": {
      "priority": 1,
      "user_message_key": "esc.red.patchy_smooth",
      "referral_urgency": "within_2_weeks",
      "referral_specialty": "dermatology"
    },
    "active": True
  },
  {
    "flag_code": "RED_04_INFECTION_INFLAMMATORY",
    "description": "Active scalp infection or inflammatory nodular disease",
    "trigger_reason": "Covers kerion (painful boggy plaque with pustules, crusting and regional lymphadenopathy, scars permanently if untreated), black-dot tinea capitis (broken hair shafts at scalp level, highly transmissible, requires oral antifungal), folliculitis decalvans, dissecting cellulitis of the scalp, and acne keloidalis nuchae. All are neutrophilic or infective processes requiring systemic prescription therapy.",
    "tier": "RED",
    "conditions": {
      "any_of": [
        {
          "field": "h5_scalp_lesions",
          "contains_any": [
            "pustules_pus_bumps",
            "boggy_swollen_painful_patch",
            "oozing_crusting",
            "open_sores_scabs",
            "black_dots",
            "keloid_bumps_nape"
          ]
        },
        {
          "field": "h13_swollen_glands_or_fever",
          "equals": "yes"
        },
        {
          "all_of": [
            {
              "field": "h5_scalp_lesions",
              "contains": "thick_scaly_plaques"
            },
            {
              "field": "h2_loss_location",
              "contains_any": [
                "patches_random"
              ]
            }
          ]
        }
      ]
    },
    "metadata": {
      "priority": 0,
      "user_message_key": "esc.red.infection",
      "referral_urgency": "within_1_week",
      "referral_specialty": "dermatology_or_general_practitioner",
      "additional_user_guidance_key": "esc.red.infection.household_note",
      "trigger_household_screening_prompt_when": {
        "field": "h14_household_or_child_similar_symptoms",
        "equals": "yes"
      }
    },
    "active": True
  },
  {
    "flag_code": "RED_05_CHEMICAL_THERMAL_INJURY",
    "description": "Acute chemical or thermal scalp/shaft injury",
    "trigger_reason": "Alkaline relaxer and lightener burns produce scalp ulceration that can scar. Hair that is gummy or dissolving when wet indicates severe cortical protein damage; further chemical or mechanical handling will amplify loss.",
    "tier": "RED",
    "conditions": {
      "any_of": [
        {
          "all_of": [
            {
              "field": "q1_treatments",
              "contains_any": [
                "relaxer",
                "bleach",
                "permanent_colour"
              ]
            },
            {
              "field": "q1b_last_treatment_recency",
              "in": [
                "lt_2w",
                "2_4w"
              ]
            },
            {
              "field": "h9_chemical_injury_signs",
              "equals": "yes"
            }
          ]
        },
        {
          "field": "h5_scalp_lesions",
          "contains_any": [
            "open_sores_scabs",
            "blisters"
          ]
        },
        {
          "field": "h9_hair_dissolving_or_gummy",
          "equals": "yes"
        }
      ]
    },
    "metadata": {
      "priority": 0,
      "user_message_key": "esc.red.chemical_injury",
      "referral_urgency": "within_72_hours",
      "referral_specialty": "dermatology_or_urgent_care",
      "hard_block_product_sale": True
    },
    "active": True
  },
  {
    "flag_code": "RED_06_ACUTE_DIFFUSE_SHEDDING",
    "description": "Acute diffuse shedding pattern (telogen effluvium picture)",
    "trigger_reason": "Telogen effluvium presents as diffuse shedding of club (white-bulbed) hairs beginning 2-3 months after a trigger: childbirth, surgery, severe illness, COVID, crash dieting, new medication, major psychological stress. Telogen fraction rises from a normal 10-15% to 30-50%; daily loss can reach 300-500 hairs. Workup is ferritin plus iron studies, TSH and free T4, vitamin D, B12, CBC. Note that ferritin is an acute-phase reactant, so a normal ferritin does not exclude iron deficiency; transferrin saturation is more sensitive.",
    "tier": "RED",
    "conditions": {
      "any_of": [
        {
          "all_of": [
            {
              "field": "g2_shed_hair_morphology",
              "equals": "mostly_bulb"
            },
            {
              "field": "g3_daily_shed_volume",
              "equals": "handfuls"
            }
          ]
        },
        {
          "all_of": [
            {
              "field": "g2_shed_hair_morphology",
              "equals": "mostly_bulb"
            },
            {
              "field": "g3_daily_shed_volume",
              "equals": "more_than_usual"
            },
            {
              "field": "h11_trigger_event_2_3_months_ago",
              "equals": "yes"
            }
          ]
        },
        {
          "all_of": [
            {
              "field": "h2_loss_location",
              "contains": "all_over"
            },
            {
              "field": "g3_daily_shed_volume",
              "equals": "handfuls"
            }
          ]
        },
        {
          "field": "h15_ponytail_circumference_visibly_reduced",
          "equals": "yes"
        }
      ]
    },
    "metadata": {
      "priority": 1,
      "user_message_key": "esc.red.diffuse_shedding",
      "referral_urgency": "within_4_weeks",
      "referral_specialty": "general_practitioner_for_bloodwork_then_dermatology",
      "referral_note_template": "shedding_bloodwork_summary",
      "suggested_workup_to_surface_to_user": [
        "full blood count",
        "ferritin and iron studies including transferrin saturation",
        "thyroid function (TSH, free T4)",
        "vitamin D",
        "vitamin B12"
      ]
    },
    "active": True
  },
  {
    "flag_code": "RED_07_FRONTAL_BAND_RECESSION",
    "description": "Band-like frontal recession with eyebrow involvement",
    "trigger_reason": "A uniform band of frontal recession with loss of the fringe hairs and eyebrow thinning suggests a scarring frontal process rather than tension. The distinguishing feature from traction alopecia is loss, rather than preservation, of the fringe.",
    "tier": "RED",
    "conditions": {
      "all_of": [
        {
          "field": "h8_hairline_receding_as_band",
          "equals": "yes"
        },
        {
          "any_of": [
            {
              "field": "h7_eyebrow_eyelash_or_body_hair_loss",
              "equals": "yes"
            },
            {
              "field": "h3_smooth_shiny_no_visible_pores",
              "equals": "yes"
            }
          ]
        }
      ]
    },
    "metadata": {
      "priority": 2,
      "user_message_key": "esc.red.frontal_band",
      "referral_urgency": "within_4_weeks",
      "referral_specialty": "dermatology"
    },
    "active": True
  },
  {
    "flag_code": "RED_08_PAEDIATRIC",
    "description": "User under 18",
    "trigger_reason": "Tinea capitis is the most common cause of paediatric scalp hair loss and requires oral antifungal therapy. Traction alopecia can begin in the preschool years. Paediatric scalp disease should not be triaged by a consumer product.",
    "tier": "RED",
    "conditions": {
      "field": "h1_age_bracket",
      "in": [
        "under_13",
        "13_17"
      ]
    },
    "metadata": {
      "priority": 0,
      "user_message_key": "esc.red.paediatric",
      "referral_urgency": "routine",
      "referral_specialty": "paediatrics_or_dermatology",
      "hard_block_product_sale": True,
      "hard_block_account_creation": True
    },
    "active": True
  },
  {
    "flag_code": "RED_09_ACTIVE_SYSTEMIC_HIGH_RISK",
    "description": "High-risk systemic context",
    "trigger_reason": "Anagen effluvium from cytotoxic therapy, discoid lupus of the scalp (a scarring alopecia), and unexplained weight loss with hair loss all require medical rather than cosmetic management.",
    "tier": "RED",
    "conditions": {
      "field": "h10_systemic_context",
      "contains_any": [
        "chemo_radiation",
        "autoimmune_lupus_active",
        "unexplained_weight_loss"
      ]
    },
    "metadata": {
      "priority": 1,
      "user_message_key": "esc.red.systemic",
      "referral_urgency": "within_2_weeks",
      "referral_specialty": "treating_physician"
    },
    "active": True
  },
  {
    "flag_code": "RED_10_PRIOR_DIAGNOSIS_SCARRING",
    "description": "User reports an existing scarring alopecia or scalp disease diagnosis",
    "trigger_reason": "A diagnosis already exists. EVOLVE must not appear to offer an alternative to it.",
    "tier": "RED",
    "conditions": {
      "field": "h12_existing_diagnosis",
      "contains_any": [
        "ccca",
        "lichen_planopilaris",
        "frontal_fibrosing",
        "discoid_lupus",
        "folliculitis_decalvans",
        "dissecting_cellulitis",
        "alopecia_areata",
        "scalp_psoriasis"
      ]
    },
    "metadata": {
      "priority": 1,
      "user_message_key": "esc.red.existing_diagnosis",
      "referral_urgency": "continue_existing_care",
      "referral_specialty": "existing_clinician"
    },
    "active": True
  },
  {
    "flag_code": "AMBER_01_EARLY_TENSION",
    "description": "Early tension pattern, no inflammatory or scarring signs",
    "trigger_reason": "",
    "tier": "AMBER",
    "conditions": {
      "all_of": [
        {
          "field": "h2_loss_location",
          "contains_any": [
            "hairline_temples",
            "nape"
          ]
        },
        {
          "field": "h3_smooth_shiny_no_visible_pores",
          "in": [
            "no",
            "unsure"
          ]
        },
        {
          "field": "h5_scalp_lesions",
          "equals_or_contains_only": [
            "none"
          ]
        },
        {
          "field": "h4_scalp_symptoms",
          "not_contains": "pain_after_styling"
        }
      ]
    },
    "metadata": {
      "protocol_constraints": {
        "force_problem": "tension_reduction",
        "forbid_styles": [
          "tight_braids",
          "cornrows_with_edge_tension",
          "sewn_weave",
          "glued_extensions",
          "tight_ponytail",
          "high_bun"
        ],
        "max_install_weeks": 0,
        "require_rest_period_weeks": 8,
        "block_products": [
          "strong_hold_edge_control",
          "heavy_gel_edge_laying"
        ]
      },
      "advisory_key": "esc.amber.early_tension",
      "mandatory_recheck_day": 56,
      "auto_escalate_to": "RED_02_TRACTION_ADVANCED",
      "auto_escalate_condition": "At day 56 recheck: no improvement in edge density self-report, OR any new pain/pustule/smooth-margin answer."
    },
    "active": True
  },
  {
    "flag_code": "AMBER_02_REFRACTORY_SCALP",
    "description": "Flaking or itch not responding to appropriate OTC antifungal use",
    "trigger_reason": "Persistent scale with hair loss can be tinea capitis, scalp psoriasis or the early inflammatory phase of a scarring alopecia rather than seborrhoeic dermatitis. Four weeks of correctly used antifungal without response is the point at which the working assumption should change.",
    "tier": "AMBER",
    "conditions": {
      "all_of": [
        {
          "field": "g1_primary_concern",
          "contains_any": [
            "scalp_flaking",
            "scalp_itch"
          ]
        },
        {
          "field": "g15_otc_antifungal_trialled_4_weeks",
          "equals": "yes"
        },
        {
          "field": "g16_otc_antifungal_response",
          "in": [
            "no_change",
            "worse"
          ]
        }
      ]
    },
    "metadata": {
      "protocol_constraints": {
        "force_problem": "scalp_dysbiosis",
        "block_products": [
          "heavy_scalp_pomade",
          "petrolatum_scalp_grease",
          "occlusive_scalp_oil"
        ]
      },
      "advisory_key": "esc.amber.refractory_scalp",
      "mandatory_recheck_day": 28
    },
    "active": True
  },
  {
    "flag_code": "AMBER_03_PROVISIONAL_BASELINE",
    "description": "Hair ID is provisional due to recent chemical service",
    "trigger_reason": "Directly per EVOLVE's own Hair ID Section A logic: the cuticle is still lifted after a chemical service, so porosity reads artificially high and the roadmap would be built on a temporary state.",
    "tier": "AMBER",
    "conditions": {
      "all_of": [
        {
          "field": "q1_treatments",
          "contains_any": [
            "permanent_colour",
            "bleach",
            "relaxer",
            "keratin"
          ]
        },
        {
          "field": "q1b_last_treatment_recency",
          "equals": "lt_2w"
        }
      ]
    },
    "metadata": {
      "protocol_constraints": {
        "porosity_confidence": "low",
        "elasticity_confidence": "low",
        "forbid_protein_treatment_until_day": 14,
        "forbid_chemical_service_until_day": 56,
        "roadmap_mode": "holding_protocol"
      },
      "advisory_key": "esc.amber.provisional_baseline",
      "mandatory_retest_day": 14,
      "retest_sections": [
        "C_porosity",
        "D_elasticity"
      ]
    },
    "active": True
  },
  {
    "flag_code": "AMBER_04_TWO_ZONE_HAIR",
    "description": "Demarcation line present (relaxed/texlaxed/heat-damaged length with natural new growth)",
    "trigger_reason": "Relaxer change is permanent on the hair it touched. New growth and processed length behave as two different fibre types with the breakage point concentrated at the line of demarcation. EVOLVE's Hair ID Section A already states this; the engine must act on it rather than only display it.",
    "tier": "AMBER",
    "conditions": {
      "any_of": [
        {
          "field": "g14_hair_state",
          "in": [
            "relaxed",
            "transitioning"
          ]
        },
        {
          "all_of": [
            {
              "field": "q1_treatments",
              "contains": "relaxer"
            },
            {
              "field": "q1b_last_treatment_recency",
              "in": [
                "1_3m",
                "gt_3m"
              ]
            }
          ]
        }
      ]
    },
    "metadata": {
      "protocol_constraints": {
        "roadmap_mode": "two_zone",
        "zone_new_growth_protocol": "moisture_and_low_manipulation",
        "zone_processed_length_protocol": "protein_moisture_alternating_plus_end_protection",
        "block_products": [
          "high_ph_clarifier_on_processed_length"
        ],
        "forbid_heat_above_c": 150
      },
      "advisory_key": "esc.amber.two_zone"
    },
    "active": True
  },
  {
    "flag_code": "AMBER_05_PREGNANCY_POSTPARTUM",
    "description": "Pregnant or within 12 months postpartum, without RED shedding criteria",
    "trigger_reason": "Postpartum shedding is a physiological telogen effluvium that resolves. The clinical risk here is commercial rather than medical: setting a growth expectation that the hair cycle, not the product, controls.",
    "tier": "AMBER",
    "conditions": {
      "all_of": [
        {
          "field": "h10_systemic_context",
          "contains_any": [
            "pregnant",
            "postpartum_12m"
          ]
        },
        {
          "field": "flag_not_fired",
          "equals": "RED_06_ACUTE_DIFFUSE_SHEDDING"
        }
      ]
    },
    "metadata": {
      "protocol_constraints": {
        "block_ingredient_classes": [
          "salicylic_acid_high_pct",
          "retinoid",
          "topical_minoxidil"
        ],
        "expectation_copy_required": True
      },
      "advisory_key": "esc.amber.pregnancy"
    },
    "active": True
  },
  {
    "flag_code": "AMBER_06_PATTERN_SUSPICIOUS",
    "description": "Gradual patterned thinning suggestive of an androgen-driven process",
    "trigger_reason": "A slowly widening part over more than a year with club-hair shedding suggests miniaturisation rather than breakage. Cosmetic care may improve fibre quality and appearance but will not alter the underlying process.",
    "tier": "AMBER",
    "conditions": {
      "all_of": [
        {
          "field": "g4_concern_duration",
          "equals": "gt_12m"
        },
        {
          "field": "h16_part_widening",
          "equals": "yes"
        },
        {
          "field": "g2_shed_hair_morphology",
          "in": [
            "mostly_bulb",
            "both"
          ]
        }
      ]
    },
    "metadata": {
      "protocol_constraints": {
        "forbid_growth_claims": True,
        "expectation_copy_required": True
      },
      "advisory_key": "esc.amber.pattern",
      "referral_specialty_suggested": "dermatology",
      "mandatory_recheck_day": 84
    },
    "active": True
  },
  {
    "flag_code": "AMBER_07_PERSISTENT_NON_RESPONDER",
    "description": "Two consecutive non-responding check-ins at adequate adherence",
    "trigger_reason": "A correctly executed cosmetic protocol that produces no measurable change over eight weeks at adequate adherence is evidence against the working hypothesis. The most common reason is that the problem was never cosmetic.",
    "tier": "AMBER",
    "conditions": {
      "all_of": [
        {
          "field": "followup.consecutive_non_responding_count",
          "gte": 2
        },
        {
          "field": "followup.mean_adherence_pct",
          "gte": 70
        }
      ]
    },
    "metadata": {
      "advisory_key": "esc.amber.non_responder",
      "action": "Re-run the full escalation screen with fresh answers, then offer derm referral regardless of outcome.",
      "evaluated_at": "follow_up_time"
    },
    "active": True
  },
  {
    "flag_code": "AMBER_08_DETERIORATION",
    "description": "Measured deterioration on protocol",
    "trigger_reason": "",
    "tier": "AMBER",
    "conditions": {
      "field": "followup.outcome_delta",
      "lte": -5
    },
    "metadata": {
      "advisory_key": "esc.amber.deterioration",
      "action": "Immediately revert to last stable protocol, re-run the full escalation screen, suppress new product recommendation until the re-screen completes.",
      "evaluated_at": "follow_up_time"
    },
    "active": True
  }
]


def upgrade() -> None:
    op.create_table(
        "escalation_flags",
        sa.Column("flag_code", sa.String(), primary_key=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("tier", sa.String(), nullable=False),
        sa.Column("conditions", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="True"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    conn = op.get_bind()
    for flag in SEED_FLAGS:
        conn.execute(
            sa.text(
                "INSERT INTO escalation_flags "
                "(flag_code, description, trigger_reason, tier, conditions, metadata, active) "
                "VALUES (:flag_code, :description, :trigger_reason, :tier, CAST(:conditions AS jsonb), CAST(:metadata AS jsonb), :active) "
                "ON CONFLICT (flag_code) DO NOTHING"
            ),
            {
                "flag_code": flag["flag_code"],
                "description": flag["description"],
                "trigger_reason": flag["trigger_reason"],
                "tier": flag["tier"],
                "conditions": json.dumps(flag["conditions"]),
                "metadata": json.dumps(flag["metadata"]),
                "active": flag["active"],
            }
        )


def downgrade() -> None:
    op.drop_table("escalation_flags")
