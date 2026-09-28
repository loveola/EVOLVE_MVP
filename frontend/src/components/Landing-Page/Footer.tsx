import evolveLogo from "../assets/evolvelogo-transparent.png";

export default function Footer() {
  return (
    <footer className="bg-coffee text-cream-200 pt-16 md:pt-20 pb-8 px-6">
      <div className="max-w-5xl mx-auto flex flex-wrap gap-12 justify-between pb-11 border-b border-cream/10">
        <div className="max-w-xs">
          <img src={evolveLogo} alt="Evolve" className="h-14 w-auto object-contain" />
          <p className="mt-4 text-sm text-taupe-200 leading-relaxed">
            A tailored hair care studio built around your unique journey —
            organic, personal, ongoing.
          </p>
        </div>

        <div>
          <h4 className="text-xs tracking-[0.16em] uppercase text-taupe-200 font-semibold mb-4">
            Studio
          </h4>
          <a href="#discovery" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            About
          </a>
          <a href="#services" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            Services
          </a>
          <a href="#testimonial" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            Stories
          </a>
        </div>

        <div>
          <h4 className="text-xs tracking-[0.16em] uppercase text-taupe-200 font-semibold mb-4">
            Connect
          </h4>
          <a href="#" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            Instagram
          </a>
          <a href="#" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            TikTok
          </a>
          <a href="#" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            hello@evolvehair.studio
          </a>
        </div>

        <div>
          <h4 className="text-xs tracking-[0.16em] uppercase text-taupe-200 font-semibold mb-4">
            Visit
          </h4>
          <a href="#" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            Abuja, FCT
          </a>
          <a href="#" className="block text-sm mb-2.5 hover:text-gold transition-colors">
            Mon – Sat, 9am – 6pm
          </a>
        </div>
      </div>

      <div className="max-w-5xl mx-auto pt-6 flex flex-wrap justify-between gap-2 text-xs text-taupe-200">
        <span>© 2026 Evolve Hair Studio. All rights reserved.</span>
        <span>Crafted for the journey your hair is already on.</span>
      </div>
    </footer>
  );
}
