# Advanced threshold handling

Keep a separate rate for every charging or measurement context. Use the most
recent context-matched window, reject plateau-only samples, and report the
calculation inputs. When contexts conflict, mark the prediction uncertain and
request a fresh measurement rather than averaging unlike contexts.
