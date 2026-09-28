import { useState, FormEvent } from "react";
import { Link } from "react-router-dom";

export default function SignUp() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Use at least 8 characters for your password.");
      return;
    }

    setSubmitting(true);
    try {
      // TODO: replace with real signup request
      await new Promise((resolve) => setTimeout(resolve, 900));
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-cream min-h-screen relative overflow-x-hidden flex flex-col">
      {/* Ambient glows, consistent with the hero */}
      <div
        className="pointer-events-none fixed -top-24 -left-24 w-[420px] h-[420px] rounded-full opacity-30 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, var(--color-gold) 0%, transparent 70%)",
        }}
      />
      <div
        className="pointer-events-none fixed -bottom-32 -right-16 w-[480px] h-[480px] rounded-full opacity-20 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, var(--color-taupe-200) 0%, transparent 70%)",
        }}
      />

      {/* Minimal top bar — just the mark, no full nav */}
      <header className="px-6 md:px-10 py-6 relative z-10">
        <Link to="/" className="font-display text-xl text-coffee tracking-wide">
          Evolve
        </Link>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 pb-16 relative z-10">
        <div className="w-full max-w-sm">
          <h1 className="font-display text-3xl md:text-4xl text-coffee text-center mb-2">
            Begin your hair journey
          </h1>
          <p className="font-body text-xs tracking-[0.08em] text-gold-deep font-semibold text-center mb-3">
            Track routine progress and make waves.
          </p>

          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-5"
            noValidate
          >
            <Field label="Name" htmlFor="name">
              <input
                id="name"
                type="text"
                autoComplete="name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-transparent border-b border-cream-200 focus:border-gold outline-none py-2 font-body text-coffee placeholder:text-taupe-200 transition-colors"
                placeholder="Your name"
              />
            </Field>

            <Field label="Email" htmlFor="email">
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-transparent border-b border-cream-200 focus:border-gold outline-none py-2 font-body text-coffee placeholder:text-taupe-200 transition-colors"
                placeholder="you@example.com"
              />
            </Field>

            <Field label="Password" htmlFor="password">
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-transparent border-b border-cream-200 focus:border-gold outline-none py-2 pr-14 font-body text-coffee placeholder:text-taupe-200 transition-colors"
                  placeholder="At least 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-0 top-1/2 -translate-y-1/2 text-xs text-taupe hover:text-coffee transition-colors"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </Field>

            {error && (
              <p role="alert" className="text-sm text-[#a5453b]">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="mt-3 w-full bg-coffee text-cream font-body text-sm tracking-wide py-3.5 rounded-full hover:bg-coffee-soft transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? "Creating your account…" : "Create account"}
            </button>
          </form>

          <p className="font-body text-xs text-taupe text-center mt-6 leading-relaxed">
            By continuing you agree to our{" "}
            <Link to="/terms" className="text-gold-deep hover:underline">
              Terms
            </Link>{" "}
            and{" "}
            <Link to="/privacy" className="text-gold-deep hover:underline">
              Privacy Policy
            </Link>
            .
          </p>

          <div className="flex items-center gap-4 my-8">
            <div className="h-px flex-1 bg-cream-200" />
            <span className="text-xs text-taupe-200">or</span>
            <div className="h-px flex-1 bg-cream-200" />
          </div>

          <p className="font-body text-sm text-taupe text-center">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-coffee font-semibold hover:text-gold-deep transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="font-body text-sm text-taupe">
        {label}
      </label>
      {children}
    </div>
  );
}
