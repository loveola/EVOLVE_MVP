import { forwardRef } from "react";
import { motion } from "framer-motion";

export default forwardRef<HTMLDivElement>(function Discovery(_, ref) {
  return (
    <section
      id="discovery"
      className="min-h-screen w-full bg-cream text-coffee flex flex-col items-center justify-center p-8 relative z-10 border-t border-cream-200"
    >
      {/* Target slot where the hero tagline visually lands and settles as this section's header */}
      <div ref={ref} className="mb-6 min-h-[70px] flex items-center justify-center" />

      <motion.div
        className="max-w-2xl text-center space-y-5"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.4 }}
        transition={{ duration: 0.7, ease: [0.65, 0.05, 0.15, 1] }}
      >
        <h2 className="font-display text-3xl md:text-4xl font-normal text-coffee">
          Tailored Care For Your Unique Lock
        </h2>
        <p className="font-body text-taupe text-lg leading-relaxed">
          From customized treatment plans to curated organic hair
          nourishment, we guide you step-by-step toward healthier, thriving
          hair — no two heads treated the same.
        </p>
        <a
          href="#services"
          className="inline-block text-sm font-semibold tracking-wide text-coffee border-b border-gold pb-1 transition-all hover:text-gold-deep hover:tracking-wider"
        >
          See how it works ↓
        </a>
      </motion.div>
    </section>
  );
});
