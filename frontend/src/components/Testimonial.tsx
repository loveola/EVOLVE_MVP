import { motion } from "framer-motion";

export default function Testimonial() {
  return (
    <section
      id="testimonial"
      className="bg-cream-200 text-center py-24 md:py-36 px-6"
    >
      <motion.blockquote
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.7, ease: [0.65, 0.05, 0.15, 1] }}
        className="font-display font-normal text-2xl md:text-4xl max-w-3xl mx-auto text-coffee leading-snug"
      >
        &ldquo;For the first time, my curls feel like they&rsquo;re finally
        being listened to.&rdquo;
      </motion.blockquote>
      <motion.p
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.7, delay: 0.15 }}
        className="mt-6 text-xs tracking-wide uppercase font-semibold text-taupe"
      >
        — A. Bello, Abuja
      </motion.p>
    </section>
  );
}
