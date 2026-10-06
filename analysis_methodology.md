# Analytical methodology

## Unit of analysis

The main performance tables are already aggregated from the original event-level learning system:

- subject level: attempts, correct answers, accuracy;
- topic level: attempts, correct answers, accuracy;
- daily level: completed tasks and XP;
- topic catalog: curriculum structure and available tasks.

## Why aggregate data is used

The original diploma system contains application-level events and identifiers. The portfolio repository keeps the analytical layer rather than exposing unnecessary application data.

## Guardrails

A topic is not treated as a product problem merely because its accuracy is low.

For prioritization:
- use a minimum observation threshold;
- compare accuracy with volume;
- explicitly flag tiny samples;
- avoid causal language without an experiment.

## Recommendation hypothesis

A useful adaptive signal can combine:

**topic weakness + recency + learning progress**

Example rule:

- high review priority when the topic has enough observations and accuracy is low;
- normal priority when performance is sufficient;
- do not escalate a topic based on one or two attempts.

## Experiment design

To validate the recommender:

**Control:** existing/baseline recommendation  
**Treatment:** adaptive recommendation

Primary metrics:
- task completion;
- learning accuracy;
- repeat practice of weak topics;
- D7 retention.

The key product question is not simply “does the model predict correctly?”, but:

> **Does personalization improve learning outcomes without increasing friction or repeatedly serving tasks the student already masters?**
