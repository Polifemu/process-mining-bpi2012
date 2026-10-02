# Process Mining Portfolio — BPI Challenge 2012

Analisi end-to-end di un event log reale con **PM4Py**: statistiche, process discovery (DFG + inductive miner), conformance checking (token replay + alignments), performance/rework e report automatico. Include un'interfaccia a domande in linguaggio naturale sui risultati.

Autore: **Filippo Polidori** — [github.com/Polifemu](https://github.com/Polifemu)

## Dataset

- **BPI Challenge 2012** (event log di richieste di prestito, azienda finanziaria olandese), distribuito da [4TU.ResearchData](https://data.4tu.nl).
- 262.200 eventi, 13.087 casi, 24 attività, 68 risorse, periodo ott. 2011 – mar. 2012.
- File non incluso nel repo: va scaricato in `data/bpi2012.xes.gz` (vedi sotto).

## Risultati principali

| Metrica | Valore |
|---|---|
| Casi / eventi / attività | 13.087 / 262.200 / 24 |
| Varianti distinte | 4.379 (top 10 = 49,3% dei casi) |
| Variante più frequente | `A_SUBMITTED → A_PARTLYSUBMITTED → A_DECLINED` (26,2%) |
| Durata media dei casi | 8,6 giorni (mediana 0,8; P90 30,5) |
| Modello (inductive miner) | 54 posti, 78 transizioni |
| Fitness (token replay, log intero) | average trace fitness 0,989 |
| Fitness (alignments, 100 casi) | average fitness 1,00 |
| Collo di bottiglia principale | `W_Nabellen offertes` — 8,0 giorni di servizio medio |

Considerazioni:
- Il **token replay** è severo su questo log (tracce incomplete + attività duplicate nel modello): 61,7% di tracce "strictly fitting", ma fitness media 0,989. Gli **alignments** risolvono le ambiguità del modello e confermano che il comportamento osservato è quasi interamente catturato dal modello. I due valori vanno letti insieme.
- La variante dominante è un **rigetto immediato** (nessuna lavorazione): è il primo candidato per automazione/straight-through processing.
- Elevato **rework** (`W_Completeren aanvraag`, `W_Nabellen offertes`): candidati per analisi root-cause sulla qualità dei dossier in ingresso.

## Struttura

```
process-mining-demo/
├── data/                  # bpi2012.xes.gz (da scaricare)
├── src/
│   ├── analysis.py        # pipeline completa → output/report.md + metrics.json
│   ├── viz.py             # visualizzazioni matplotlib/networkx (nessun graphviz richiesto)
│   └── ask.py             # Q&A sui risultati (regole + LLM opzionale)
├── output/
│   ├── report.md          # report automatico
│   ├── metrics.json       # tutte le metriche in formato macchina
│   ├── figures/           # DFG (frequenze e tempi), Petri net, varianti, durate
│   └── models/            # inductive.pnml (Petri net)
└── requirements.txt
```

## Avvio

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# scarica il log (esempio con curl; il link ufficiale è sulla pagina 4TU del BPI Challenge 2012)
curl -L "<url-file-xes>" -o data/bpi2012.xes.gz

python src/analysis.py --log data/bpi2012.xes.gz --out output
python src/ask.py "quanti casi ci sono?"          # una domanda e via
python src/ask.py                                  # modalità interattiva
python src/ask.py --llm "perché il caso medio dura così tanto?"   # richiede OPENAI_API_KEY
```

## Interfaccia a domande

`ask.py` risponde su: casi/eventi, varianti, fitness, colli di bottiglia, durata dei casi, rework, risorse, modello. Con `--llm` e `OPENAI_API_KEY` le domande libere vengono risolte da un LLM ancorato a `metrics.json` (grounded, senza hallucination sui numeri).

## Note

- Le visualizzazioni di processo sono renderizzate con networkx/matplotlib: **nessuna dipendenza da Graphviz**.
- PM4Py è AGPL v3: per uso commerciale closed-source serve licenza commerciale (l'analisi in sé è riproducibile con licenza commerciale o strumenti alternativi).
- L'export BPMN nativo di PM4Py richiede Graphviz (`dot`) e viene saltato automaticamente se assente; la Petri net è esportata in PNML.
