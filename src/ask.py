import json
import os
import sys
from pathlib import Path

METRICS = Path(__file__).resolve().parent.parent / "output" / "metrics.json"


def load_metrics():
    if not METRICS.exists():
        sys.exit("metrics.json non trovato: esegui prima `python src/analysis.py`")
    return json.loads(METRICS.read_text())


def answer(m, q):
    ql = q.lower()
    d = m["dataset"]

    def has(*words):
        return any(w in ql for w in words)

    if has("quanti", "how many", "numero") and has("cas", "case"):
        return f"Il log contiene {d['cases']:,} casi e {d['events']:,} eventi, con {d['activities']} attività distinte e {d['resources']} risorse."
    if has("event"):
        return f"Eventi totali: {d['events']:,}."
    if has("variant", "percors", "path", "tracc"):
        top = m["variants"]["top"][:3]
        lines = [f"{m['variants']['total']:,} varianti distinte; le prime 10 coprono il {m['variants']['coverage_top10']}% dei casi."]
        for v in top:
            lines.append(f"- {v['count']:,} casi ({v['share']}%): {' → '.join(v['activities'])}")
        return "\n".join(lines)
    if has("fitness", "conformance", "conform", "allineam", "alignment", "replay"):
        c = m["conformance_token_replay"]
        a = m["conformance_alignments_sample"]
        return (f"Token replay (intero log): {c}\n"
                f"Alignments (campione di {a['sample_size']} casi): {a}")
    if has("lent", "slow", "bottleneck", "collo", "servizio"):
        lines = ["Top attività per tempo di servizio medio:"]
        for b in m["bottlenecks"][:5]:
            lines.append(f"- {b['activity']}: {b['mean_service']} medi ({b['occurrences']:,} occorrenze), attesa media successiva {b['mean_wait']}")
        return "\n".join(lines)
    if has("durata", "duration", "tempo", "throughput", "lead"):
        cd = m["case_duration_days"]
        return (f"Durata dei casi (giorni): media {cd['mean']}, mediana {cd['median']}, "
                f"P90 {cd['p90']}, P99 {cd['p99']}, massimo {cd['max']}.")
    if has("rework", "rielabor", "rielabo", "ripet"):
        r = m["rework"]
        top = ", ".join(f"{t['activity']} ({t['cases']:,})" for t in r["top_activities"][:5]) or "nessuna"
        return f"Casi con rielaborazioni: {r['cases_with_rework']:,}. Attività più ripetute: {top}."
    if has("risors", "resource", "utent", "chi lavora"):
        top = ", ".join(f"{r['resource']} ({r['events']:,} eventi)" for r in m["top_resources"][:5])
        return f"Risorse più attive: {top}."
    if has("modello", "model", "petri", "rete"):
        mo = m["model"]
        return (f"Modello scoperto con inductive miner: {mo['places']} posti, "
                f"{mo['transitions']} transizioni, {mo['arcs']} archi. File: output/models/inductive.pnml e .bpmn.")
    if has("aiuto", "help", "cosa puoi", "domande"):
        return ("Prova con: \"quanti casi ci sono?\", \"varianti più frequenti\", \"fitness del modello\", "
                "\"attività più lente\", \"durata dei casi\", \"rielaborazioni\", \"risorse più attive\", \"modello Petri\".")
    return ("Non ho capito. Prova con: casi, varianti, fitness, collo di bottiglia, durata, rework, "
            "risorse, modello. Oppure usa --llm con OPENAI_API_KEY per le domande libere.")


def answer_llm(m, q):
    try:
        from openai import OpenAI
    except ImportError:
        return None
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    client = OpenAI(api_key=key)
    context = json.dumps(m, default=str)[:12000]
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "Rispondi in italiano, in modo conciso, basandoti SOLO sui dati di processo forniti in JSON."},
            {"role": "user", "content": f"Dati: {context}\n\nDomanda: {q}"},
        ],
        temperature=0,
    )
    return r.choices[0].message.content


def main():
    m = load_metrics()
    use_llm = "--llm" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--llm"]
    if args:
        q = " ".join(args)
        out = answer_llm(m, q) if use_llm else None
        print(out or answer(m, q))
        return
    print("Parla con il processo (digitare 'esci' per uscire)")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("esci", "exit", "quit"):
            break
        if not q:
            continue
        out = answer_llm(m, q) if use_llm else None
        print(out or answer(m, q))


if __name__ == "__main__":
    main()
