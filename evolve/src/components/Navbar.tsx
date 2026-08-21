import { forwardRef, useState } from "react";
import { Menu, X } from "lucide-react";
import evolveLogo from "../assets/evolvelogo-transparent.png";
import { buttonVariants } from "./ui/button";
import { cn } from "@/lib/utils";

const links = [
  { href: "#discovery", label: "About" },
  { href: "#services", label: "Services" },
  { href: "#testimonial", label: "Stories" },
  { href: "#cta", label: "Contact" },
];

export default forwardRef<HTMLImageElement>(function Navbar(_, ref) {
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 w-full z-50 h-28 flex items-center justify-between px-5 md:px-10 bg-cream/85 backdrop-blur-md border-b border-cream-200">
      <div className="flex items-center h-11">
        <img
          ref={ref}
          src={evolveLogo}
          alt="Evolve"
          className="h-20 md:h-24 w-auto object-contain origin-top-left cursor-pointer will-change-transform"
        />
      </div>

      <div className="flex items-center gap-6 md:gap-10">
        <div
          className={`
            fixed md:static top-28 left-0 w-full md:w-auto
            flex flex-col md:flex-row items-start md:items-center
            gap-6 md:gap-10 px-6 md:px-0 py-8 md:py-0
            bg-cream md:bg-transparent border-b md:border-none border-cream-200
            transition-all duration-300 ease-[cubic-bezier(.65,.05,.15,1)]
            ${open ? "opacity-100 visible translate-y-0" : "opacity-0 invisible -translate-y-2 md:opacity-100 md:visible md:translate-y-0"}
          `}
        >
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="relative font-body text-sm md:text-sm font-medium text-coffee group"
            >
              {l.label}
              <span className="absolute left-0 -bottom-0.5 h-px w-0 bg-gold transition-all duration-300 group-hover:w-full" />
            </a>
          ))}
        </div>

        <a
          href="#cta"
          className={cn(buttonVariants({ variant: "outline", size: "sm" }), "hidden sm:inline-flex")}
        >
          Book a Consultation
        </a>

        <button
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="md:hidden text-coffee"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
    </nav>
  );
});