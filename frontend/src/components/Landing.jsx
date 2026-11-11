import { ShieldCheck, BookOpenCheck, Stethoscope, Ban, Siren, ExternalLink } from 'lucide-react'
import BrandMark from './BrandMark.jsx'
import RangeGauge from './RangeGauge.jsx'
import StatusChip from './StatusChip.jsx'

/** The real sequence a report goes through (spec §4), shown as steps on a track. */
const STEPS = [
  {
    title: 'Read',
    text: 'The PDF is read in memory. It is never saved, and scanned images are turned away politely.',
  },
  {
    title: 'Copy',
    text: 'An AI model copies each test, value, unit and range exactly as printed. It does not interpret.',
  },
  {
    title: 'Check',
    text: "Plain code compares each number with your lab's own range and decides low, normal or high.",
  },
  {
    title: 'Explain',
    text: 'The AI writes calm, plain explanations, seeing only the checked numbers, never the raw file.',
  },
]

const PRINCIPLES = [
  {
    icon: Stethoscope,
    title: 'It never diagnoses',
    text: 'MedBridge explains what a test measures and what a flag means. Decisions stay with your doctor.',
  },
  {
    icon: BookOpenCheck,
    title: 'Ranges come from your lab',
    text: 'Low, normal and high are worked out by code using the range printed on your report, not invented by AI.',
  },
  {
    icon: ExternalLink,
    title: 'Answers show their sources',
    text: 'The assistant answers only from 30 reviewed articles and links each claim to its source.',
  },
  {
    icon: Ban,
    title: 'Nothing is kept',
    text: 'No accounts, no database, no saved files. Close the tab and your report is gone.',
  },
  {
    icon: Siren,
    title: 'Emergencies get a straight answer',
    text: 'Describe an emergency and MedBridge tells you to contact emergency services, without asking the AI.',
  },
]

/**
 * Landing page shown before the app. Uses the app's own components for its visuals,
 * so what people see here is exactly what the tool produces.
 *
 * @param {{ onOpen: (tab?: string) => void }} props
 */
export default function Landing({ onOpen }) {
  return (
    <div className="landing">
      <header className="landing-bar">
        <div className="landing-bar__inner">
          <div className="brand">
            <BrandMark />
            <span>MedBridge</span>
          </div>
          <nav aria-label="Page sections" className="landing-bar__nav">
            <a href="#how">How it works</a>
            <a href="#careful">Safety</a>
            <button type="button" className="btn btn--primary btn--small" onClick={() => onOpen()}>
              Open MedBridge
            </button>
          </nav>
        </div>
      </header>

      <main>
        {/* ---------- Hero: the transformation ---------- */}
        <section className="l-hero" aria-labelledby="l-hero-title">
          <div className="l-wrap l-hero__grid">
            <div>
              <h1 id="l-hero-title" className="l-hero__title">
                Lab reports, in plain words.
              </h1>
              <p className="l-hero__lede">
                MedBridge reads your lab report, shows every result against your lab&apos;s own
                range, and explains what it means in language you don&apos;t need a medical degree
                for. Then it helps you prepare questions for your doctor.
              </p>
              <div className="button-row l-hero__actions">
                <button type="button" className="btn btn--primary" onClick={() => onOpen('report')}>
                  Try a sample report
                </button>
                <button type="button" className="btn btn--secondary" onClick={() => onOpen('ask')}>
                  Ask about a test
                </button>
              </div>
            </div>

            <figure className="transform" aria-label="How one line of a lab report becomes clear">
              <div className="transform__raw" aria-label="As printed on the report">
                <span>Haemoglobin</span>
                <span>10.8</span>
                <span>g/dL</span>
                <span>12.0 – 15.5</span>
                <span className="transform__flag">L</span>
              </div>
              <div className="transform__arrow" aria-hidden="true" />
              <div className="transform__clear">
                <div className="transform__head">
                  <span className="transform__name">Haemoglobin</span>
                  <StatusChip status="low" />
                </div>
                <RangeGauge
                  size="hero"
                  value={10.8}
                  low={12}
                  high={15.5}
                  status="low"
                  valueText="10.8"
                  label="Haemoglobin 10.8 g/dL, below the lab's range of 12.0 to 15.5"
                />
                <p className="transform__sentence">
                  Haemoglobin carries oxygen in your blood. Yours is a little below the lab&apos;s
                  range, which your doctor may want to talk through with you.
                </p>
              </div>
            </figure>
          </div>
        </section>

        {/* ---------- Features ---------- */}
        <section className="l-section" aria-labelledby="l-features-title">
          <div className="l-wrap">
            <h2 id="l-features-title" className="l-section__title">
              One upload, three ways to understand it
            </h2>

            <div className="feature">
              <div className="feature__text">
                <h3>Every result, explained</h3>
                <p>
                  A short overview of the whole report, then each test in turn: what it measures,
                  what your number means, and why it might be flagged. Simple or detailed wording,
                  your choice.
                </p>
              </div>
              <div className="feature__demo" aria-hidden="true">
                <div className="mini-card">
                  <div className="mini-card__row">
                    <strong>Hematocrit (PCV)</strong>
                    <span className="muted">33.1 %</span>
                    <StatusChip status="low" />
                  </div>
                  <p className="mini-card__label">What it measures</p>
                  <p>The share of your blood made up of red blood cells.</p>
                  <p className="mini-card__label">Why it might be flagged</p>
                  <p>
                    Values below range can have many causes, such as low iron. Only your doctor can
                    tell what applies to you.
                  </p>
                </div>
              </div>
            </div>

            <div className="feature feature--flip">
              <div className="feature__text">
                <h3>A dashboard you can read at a glance</h3>
                <p>
                  Each value sits on a bar against the lab&apos;s range, grouped the way your report
                  groups them. Filter to just the results outside the range.
                </p>
              </div>
              <div className="feature__demo" aria-hidden="true">
                <div className="mini-dash">
                  {[
                    ['LDL Cholesterol', 162, null, 100, 'high', '162 mg/dL'],
                    ['HDL Cholesterol', 38, 40, null, 'low', '38 mg/dL'],
                    ['Platelet Count', 245000, 150000, 410000, 'normal', '2,45,000 /µL'],
                  ].map(([name, v, lo, hi, s, txt]) => (
                    <div key={name} className="mini-dash__row">
                      <div className="mini-card__row">
                        <strong>{name}</strong>
                        <span className="muted">{txt}</span>
                        <StatusChip status={s} />
                      </div>
                      <RangeGauge value={v} low={lo} high={hi} status={s} label={name} />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="feature">
              <div className="feature__text">
                <h3>Questions answered, with sources</h3>
                <p>
                  Ask what MCV means or why some tests need fasting. Answers come only from a
                  curated library of patient articles, and every claim links to where it came from.
                </p>
              </div>
              <div className="feature__demo" aria-hidden="true">
                <div className="mini-chat">
                  <p className="mini-chat__q">What is the difference between LDL and HDL?</p>
                  <div className="mini-chat__a">
                    <p>
                      LDL carries cholesterol to your cells and is often called &ldquo;bad&rdquo;
                      cholesterol
                      <sup className="citation">1</sup>. HDL carries extra cholesterol back to the
                      liver, which is why it is called &ldquo;good&rdquo;
                      <sup className="citation">2</sup>.
                    </p>
                    <div className="mini-chat__source">
                      <span className="source-card__num">1</span>
                      <span>
                        <strong>LDL Cholesterol</strong>
                        <span className="muted"> MedlinePlus</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- How it works: a real sequence ---------- */}
        <section id="how" className="l-section l-section--tinted" aria-labelledby="l-how-title">
          <div className="l-wrap">
            <h2 id="l-how-title" className="l-section__title">
              What happens to your report
            </h2>
            <p className="l-section__lede">
              The AI never decides whether a number is high or low. That job belongs to plain,
              testable code, and the AI only writes explanations once the numbers are checked.
            </p>
            <ol className="steps">
              {STEPS.map((s, i) => (
                <li key={s.title} className="step">
                  <span className="step__dot" aria-hidden="true">
                    {i + 1}
                  </span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ---------- Safety ---------- */}
        <section id="careful" className="l-section" aria-labelledby="l-careful-title">
          <div className="l-wrap">
            <h2 id="l-careful-title" className="l-section__title">
              Built to be careful
            </h2>
            <ul className="principles">
              {PRINCIPLES.map(({ icon: Icon, title, text }) => (
                <li key={title}>
                  <Icon size={22} strokeWidth={1.75} aria-hidden="true" />
                  <div>
                    <h3>{title}</h3>
                    <p>{text}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ---------- About ---------- */}
        <section className="l-section l-section--tinted" aria-labelledby="l-about-title">
          <div className="l-wrap l-about">
            <div>
              <h2 id="l-about-title" className="l-section__title">
                About the project
              </h2>
              <p>
                MedBridge is an academic digital-health project exploring how large language models
                and retrieval-augmented generation can make medical information easier to
                understand, without replacing clinical judgement.
              </p>
              <p>
                In testing, the knowledge search found the right article within its top three
                results for every one of 20 sample questions, and declined off-topic questions
                instead of guessing.
              </p>
            </div>
            <dl className="stack-list">
              <div>
                <dt>Interface</dt>
                <dd>React and Vite</dd>
              </div>
              <div>
                <dt>Server</dt>
                <dd>FastAPI, with exactly two endpoints</dd>
              </div>
              <div>
                <dt>Language model</dt>
                <dd>Groq-hosted LLM, structured JSON output</dd>
              </div>
              <div>
                <dt>Knowledge search</dt>
                <dd>MiniLM embeddings with vector search over 30 articles</dd>
              </div>
              <div>
                <dt>References</dt>
                <dd>MedlinePlus, NHS, Testing.com, Cleveland Clinic</dd>
              </div>
            </dl>
          </div>
        </section>

        {/* ---------- Closing ---------- */}
        <section className="l-close" aria-labelledby="l-close-title">
          <div className="l-wrap">
            <h2 id="l-close-title" className="l-close__title">
              Bring your next report to your doctor with better questions.
            </h2>
            <button type="button" className="btn btn--primary" onClick={() => onOpen('report')}>
              Open MedBridge
            </button>
            <p className="privacy-note small">
              <ShieldCheck size={16} aria-hidden="true" />
              Sample reports are synthetic. Your own file is processed for the session only.
            </p>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <div className="l-wrap">
          <p>
            MedBridge provides educational information only and is not a substitute for professional
            medical advice, diagnosis, or treatment. Always discuss your results with a qualified
            healthcare provider. If you think you may have a medical emergency, contact your local
            emergency number immediately.
          </p>
          <p className="muted">An academic digital health course project. Not a medical device.</p>
        </div>
      </footer>
    </div>
  )
}
