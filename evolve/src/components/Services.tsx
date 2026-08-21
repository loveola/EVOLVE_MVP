import { motion } from "framer-motion";

const steps = [
  {
    num: "01",
    title: "Diagnose",
    body: "A full scalp and strand analysis — porosity, density, damage history — so nothing is guessed.",
  },
  {
    num: "02",
    title: "Prescribe",
    body: "A regimen built for your hair alone: ingredients, order, and frequency, nothing generic.",
  },
  {
    num: "03",
    title: "Nourish",
    body: "In-studio organic treatments that repair from the root, formulated without harsh actives.",
  },
  {
    num: "04",
    title: "Sustain",
    body: "Ongoing check-ins that adjust your plan as your hair — and its needs — evolve.",
  },
];

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.12 },
  },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.65, 0.05, 0.15, 1] } },
};

export default function Services() {
  return (
    <section
      id="services"
      className="bg-cream text-center py-28 md:py-40 px-6"
    >
      <motion.p
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="font-body text-xs tracking-[0.24em] uppercase text-gold-deep font-semibold"
      >
        The Journey
      </motion.p>
      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="font-display font-normal text-3xl md:text-5xl mt-3 mb-14 md:mb-20"
      >
        Four steps to healthier hair
      </motion.h2>

      <motion.div
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.2 }}
        className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border-t border-cream-200 text-left"
      >
        {steps.map((s, i) => {
          const rightBorderSm = i % 2 === 0 ? "sm:border-r" : "";
          const rightBorderLg = i !== steps.length - 1 ? "lg:border-r" : "";
          return (
            <motion.div
              key={s.num}
              variants={item}
              className={`p-8 border-b border-cream-200 transition-colors duration-300 hover:bg-cream-200 ${rightBorderSm} ${rightBorderLg}`}
            >
              <span className="block font-display text-sm text-gold-deep mb-6">
                {s.num}
              </span>
              <h3 className="font-display font-normal text-2xl text-coffee mb-3">
                {s.title}
              </h3>
              <p className="text-sm text-taupe leading-relaxed">{s.body}</p>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}
