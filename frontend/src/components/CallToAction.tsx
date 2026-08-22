import { motion } from "framer-motion";
import { Button } from "./ui/button";

export default function CallToAction() {
  return (
    <section id="cta" className="bg-cream text-center py-28 md:py-44 px-6">
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.6 }}
        transition={{ duration: 0.7 }}
        className="font-display font-normal text-3xl md:text-5xl lg:text-6xl max-w-2xl mx-auto text-coffee"
      >
        Ready to begin your hair journey?
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.6 }}
        transition={{ duration: 0.7, delay: 0.1 }}
        className="mt-4 text-taupe text-sm"
      >
        First-time clients receive a complimentary scalp consultation.
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.6 }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="mt-9"
      >
        <Button size="lg" className="min-w-[220px]">
          Book your consultation
        </Button>
      </motion.div>
    </section>
  );
}
