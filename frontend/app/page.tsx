import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <p className="font-mono text-xs tracking-widest text-signal uppercase mb-4">
        // cloudops ai
      </p>
      <h1 className="text-4xl sm:text-5xl font-semibold text-ink max-w-2xl leading-tight mb-5">
        An autonomous AI Cloud Operations Engineer
      </h1>
      <p className="text-faint max-w-xl mb-10">
        Upload Terraform, Kubernetes YAML, Docker Compose, or cloud error
        logs. Four specialist agents analyze security, networking, cost, and
        reliability — then a report agent hands you a fix.
      </p>
      <Link
        href="/dashboard"
        className="font-mono text-sm px-6 py-3 rounded-md bg-signal text-void font-semibold hover:opacity-90 transition-opacity"
      >
        Open dashboard →
      </Link>
    </main>
  );
}
