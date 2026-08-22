import { useRef } from "react";
import { motion } from "framer-motion";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger, useGSAP);

export default function Philosophy() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const pathRef = useRef<SVGPathElement>(null);

  useGSAP(
    () => {
      const path = pathRef.current;
      if (!path) return;

      const reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;

      const length = path.getTotalLength();
      gsap.set(path, {
        strokeDasharray: length,
        strokeDashoffset: reduceMotion ? 0 : length,
      });

      if (reduceMotion) return;

      gsap.to(path, {
        strokeDashoffset: 0,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 90%",
          end: "bottom 40%",
          scrub: 1,
        },
      });
    },
    { scope: sectionRef }
  );

  return (
    <section
      ref={sectionRef}
      className="relative bg-coffee text-cream overflow-hidden py-28 md:py-40 px-6 text-center"
    >
      <svg
        className="absolute inset-0 pointer-events-none"
        width="100%"
        height="100%"
        viewBox="0 0 1000 500"
        preserveAspectRatio="none"
      >
        <path
          ref={pathRef}
          d="M -50 60 C 150 10, 250 150, 450 120 S 750 20, 1050 90"
          fill="none"
          stroke="#c6992e"
          strokeWidth="1.4"
          strokeLinecap="round"
          opacity="0.55"
        />
      </svg>

      <motion.blockquote
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.4 }}
        transition={{ duration: 0.8, ease: [0.65, 0.05, 0.15, 1] }}
        className="relative z-10 font-display font-normal text-3xl md:text-5xl lg:text-6xl leading-tight max-w-4xl mx-auto"
      >
        Hair isn&rsquo;t maintained.
        <br />
        It&rsquo;s understood.
      </motion.blockquote>

      <motion.p
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.4 }}
        transition={{ duration: 0.8, delay: 0.15, ease: [0.65, 0.05, 0.15, 1] }}
        className="relative z-10 mt-7 text-taupe-200 text-base md:text-lg max-w-xl mx-auto leading-relaxed"
      >
        Every strand carries a history — of water, climate, stress, and care.
        We start there, not with a shelf of products, but with what your hair
        is actually telling us.
      </motion.p>
    </section>
  );
}
