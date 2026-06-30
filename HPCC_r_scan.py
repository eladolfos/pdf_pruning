import pruning_tools as pt
import pandas as pd
from pathlib import Path
import numpy as np

# Loading vectors
data_folder = Path("CT25altData")
vec_filename = "pq125a_CT25alNNLO_vectors.tsv"

df_vectors_pre = pd.read_csv(data_folder / vec_filename, skiprows=1, sep='\t', header=None)
df_vectors=df_vectors_pre.drop(df_vectors_pre.columns[0], axis=1)

#df_vectors

met_filename = "pq125a_CT25alNNLO_Metadata.tsv"
metadata = pd.read_csv(data_folder / met_filename, skiprows=2,  sep="\s+")
metadata


data_folder = Path("CT25altData")

metadata = pd.read_csv(data_folder / "pq125a_CT25alNNLO_Metadata.tsv", skiprows=2, sep=r"\s+")
metadata["member_idx"] = metadata["Filename"].str.extract(r"(\d+)$").astype(int)
metadata = metadata.set_index("member_idx").sort_index().reset_index(drop=True) 
#metadata


df_vectors = pd.read_csv(data_folder / "pq125a_CT25alNNLO_vectors.tsv", sep="\t")
df_vectors = df_vectors.loc[:, ~df_vectors.columns.str.startswith("member_idx.")]
df_vectors = df_vectors.set_index("member_idx").drop(columns=["filename"]).sort_index().reset_index(drop=True) 
#df_vectors


# Scaning many R values
vec = df_vectors.values
chi2List =metadata["Chi2F"].values

# Crear el linspace original
demo_R = np.linspace(0.1, 10, 100)

# Forzar que 1.34 esté incluido
demo_R = np.sort(np.unique(np.append(demo_R, 1.34)))

 
R_scan = pt.scan_R_parallel(vectors=vec, chi2=chi2List, metric=pt.pdf_dissimilarity, rec_crit="best_chi2", R_values=demo_R)

np.save('R_scan.npy', R_scan)