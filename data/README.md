# Dataset files

Copy the supplied clinical-trial CSV files into this directory:

- DM.csv, AE.csv, LB.csv, VS.csv, EX.csv, EG.csv
- CM.csv, MH.csv, DS.csv
- corrections.csv, reference_ranges.csv, cuts.csv

The server automatically loads CSV files from this directory at startup. The dashboard can also send CSV text to `/api/load`.
