# Wireless, DSP, and 6G Foundations

OFDM packs many narrow subcarriers into one symbol. A cyclic prefix copies the tail onto the front so delayed copies still look circular. That prefix is not free: samples spent on CP are samples not spent on new data.

Work a 64-point FFT with 52 occupied bins and CP=16. Symbol length is 80 samples. Overhead is 16/80. Occupancy is 52/64. Null bins exist on purpose (guards).

6G slogans do not replace this arithmetic. This seed does not claim a 6G air interface implementation — it claims you can compute overhead offline.
