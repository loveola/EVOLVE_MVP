import { useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import Navbar from "./Navbar";
import Discovery from "./Discovery";
import Philosophy from "./Philosophy";
import Services from "./Services";
import Testimonial from "./Testimonial";
import CallToAction from "./CallToAction";
import Footer from "./Footer";

gsap.registerPlugin(ScrollTrigger, useGSAP);

export default function Landing() {
  const heroRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLImageElement>(null);
  const taglineRef = useRef<HTMLParagraphElement>(null);
  const kickerRef = useRef<HTMLParagraphElement>(null);
  const taglineSlotRef = useRef<HTMLDivElement>(null);
  const blob1Ref = useRef<HTMLDivElement>(null);
  const blob2Ref = useRef<HTMLDivElement>(null);
  const arcPathRef = useRef<SVGPathElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const logo = logoRef.current;
      const tagline = taglineRef.current;
      const taglineSlot = taglineSlotRef.current;
      const kicker = kickerRef.current;
      const blob1 = blob1Ref.current;
      const blob2 = blob2Ref.current;
      const arcPath = arcPathRef.current;
      const progress = progressRef.current;

      if (!logo || !tagline || !taglineSlot) return;

      const reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;

      if (reduceMotion) {
        gsap.set(logo, { clearProps: "all" });
        return;
      }

      let tl: gsap.core.Timeline | undefined;

      const build = () => {
        // Tear down any previous instance before rebuilding (resize, StrictMode
        // double-invoke in dev, etc.) so we never end up with two pins stacked.
        if (tl) {
          tl.scrollTrigger?.kill();
          tl.kill();
          tl = undefined;
        }

        // Clear any leftover transform so we measure the logo's true resting
        // position and size, not a transformed one from a previous build.
        gsap.set(logo, { clearProps: "transform" });

        const logoBounds = logo.getBoundingClientRect();
        const targetHeroHeight = window.innerWidth >= 768 ? 450 : 280;
        const scaleFactor = targetHeroHeight / (logoBounds.height || 1);

        const initialX =
          window.innerWidth / 2 -
          logoBounds.left -
          (logoBounds.width * scaleFactor) / 2;
        const initialY =
          window.innerHeight / 2 -
          logoBounds.top -
          (logoBounds.height * scaleFactor) / 2 -
          40;

        const taglineBounds = tagline.getBoundingClientRect();
        const slotBounds = taglineSlot.getBoundingClientRect();
        const taglineDeltaY = slotBounds.top - taglineBounds.top;

        gsap.set(logo, {
          x: initialX,
          y: initialY,
          scale: scaleFactor,
          transformOrigin: "top left",
        });

        tl = gsap.timeline({
          scrollTrigger: {
            trigger: heroRef.current,
            start: "top top",
            end: "+=120%",
            scrub: 1,
            pin: true,
            anticipatePin: 1,
            invalidateOnRefresh: true,
          },
        });

        // Logo: Hero center -> top-left Navbar position
        tl.fromTo(
          logo,
          { x: initialX, y: initialY, scale: scaleFactor },
          { x: 0, y: 0, scale: 1, ease: "power2.inOut" },
          0
        )
          // Tagline: down into the Discovery section slot
          .to(
            tagline,
            { y: taglineDeltaY, scale: 1.15, ease: "power2.inOut" },
            0
          )
          // Kicker fades as the sequence begins
          .to(kicker, { opacity: 0, y: -16, ease: "power1.out" }, 0);

        // Ambient motion so the pinned scroll has something happening
        // throughout, not just at the very start/end.
        if (blob1) {
          tl.fromTo(
            blob1,
            { x: 0, y: 0 },
            { x: -90, y: -60, ease: "none" },
            0
          );
        }
        if (blob2) {
          tl.fromTo(
            blob2,
            { x: 0, y: 0 },
            { x: 80, y: 70, ease: "none" },
            0
          );
        }
        if (arcPath) {
          const len = arcPath.getTotalLength();
          gsap.set(arcPath, { strokeDasharray: len, strokeDashoffset: len });
          tl.fromTo(
            arcPath,
            { strokeDashoffset: len },
            { strokeDashoffset: 0, ease: "none" },
            0
          );
        }
        if (progress) {
          tl.fromTo(
            progress,
            { scaleX: 0 },
            { scaleX: 1, ease: "none", transformOrigin: "left center" },
            0
          );
        }
      };

      // The logo's HEIGHT is fixed by CSS (h-20/h-24), but its WIDTH is `auto` —
      // that's only correct once the browser has actually decoded the image.
      // Measuring before that gives a wrong (often 0) width and throws off centering.
      if (logo.complete && logo.naturalWidth > 0) {
        build();
      } else {
        logo.addEventListener("load", build, { once: true });
      }

      let resizeTimer: ReturnType<typeof setTimeout>;
      const onResize = () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(build, 200);
      };
      window.addEventListener("resize", onResize);

      return () => {
        window.removeEventListener("resize", onResize);
        logo.removeEventListener("load", build);
        tl?.scrollTrigger?.kill();
        tl?.kill();
      };
    },
    { scope: heroRef, dependencies: [] }
  );

  return (
    <div className="bg-cream min-h-screen relative overflow-x-hidden">
      <Navbar ref={logoRef} />

      {/* Hero */}
      <section
        ref={heroRef}
        className="h-screen w-full flex flex-col items-center justify-center px-4 relative overflow-hidden"
      >
        {/* Ambient parallax glows — pure background texture, sits behind everything */}
        <div
          ref={blob1Ref}
          className="pointer-events-none absolute -top-24 -left-24 w-[420px] h-[420px] rounded-full opacity-40 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, var(--color-gold) 0%, transparent 70%)",
          }}
        />
        <div
          ref={blob2Ref}
          className="pointer-events-none absolute -bottom-32 -right-16 w-[480px] h-[480px] rounded-full opacity-30 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, var(--color-taupe-200) 0%, transparent 70%)",
          }}
        />

        {/* Thin arc drawn in behind the logo as you scroll — echoes the strand
            motif from the Philosophy section, gives the eye something to
            follow through the middle of the pin */}
        <svg
          className="pointer-events-none absolute inset-0 mx-auto my-auto"
          width="100%"
          height="100%"
          viewBox="0 0 800 800"
          preserveAspectRatio="xMidYMid meet"
        >
          <path
            ref={arcPathRef}
            d="M 130 560 C 260 680, 540 680, 670 560 C 780 460, 780 300, 670 200"
            fill="none"
            stroke="#c6992e"
            strokeWidth="1.2"
            strokeLinecap="round"
            opacity="0.5"
          />
        </svg>

        <p
          ref={kickerRef}
          className="font-body text-xs tracking-[0.24em] uppercase text-gold-deep font-semibold text-center absolute top-10 md:top-12"
        >
          A Personalized Hair Ritual
        </p>

        <p
          ref={taglineRef}
          className="font-display text-2xl md:text-3xl text-coffee tracking-wide z-20 text-center mt-52 md:mt-64 will-change-transform"
        >
          Discover your hair journey
        </p>

        <div className="absolute bottom-11 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2.5 text-taupe">
          <span className="text-[11px] tracking-[0.2em] uppercase">Scroll</span>
          <div className="w-px h-9 bg-taupe-200 relative overflow-hidden scroll-cue-drip" />
        </div>

        {/* Scroll-progress line — fills across the bottom of the pinned hero */}
        <div className="absolute bottom-0 left-0 w-full h-px bg-cream-200">
          <div
            ref={progressRef}
            className="h-full w-full bg-gold"
            style={{ transform: "scaleX(0)" }}
          />
        </div>
      </section>

      <Discovery ref={taglineSlotRef} />
      <Philosophy />
      <Services />
      <Testimonial />
      <CallToAction />
      <Footer />
    </div>
  );
}