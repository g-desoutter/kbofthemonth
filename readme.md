<div align="center">

# KB of the Month

**Les mises à jour de sécurité mensuelles pour Windows Server, en JSON.**

Extraction automatisée du flux CVRF officiel du MSRC, republié chaque mois
sous forme d'API statique consommable par vos scripts d'inventaire.

[![Update KBs](https://img.shields.io/github/actions/workflow/status/g-desoutter/kbofthemonth/update_kbs.yml?branch=main&label=update&style=flat-square)](https://github.com/g-desoutter/kbofthemonth/actions)
[![Pages](https://img.shields.io/badge/endpoint-live-2563eb?style=flat-square)](https://g-desoutter.github.io/kbofthemonth/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

[**Consulter les KB du mois →**](https://g-desoutter.github.io/kbofthemonth/)

</div>

---

## Le problème

Chaque Patch Tuesday, vérifier qu'un parc Windows Server est à jour suppose de
savoir *quelle KB* s'applique à *quelle édition*. L'information existe dans le
flux CVRF du MSRC, mais elle y est noyée dans un document de plusieurs milliers
de lignes mêlant toutes les gammes de produits Microsoft, où les correctifs
sont indexés par vulnérabilité et non par système.

Ce projet fait l'extraction une fois, automatiquement, et expose le résultat.

## L'endpoint

```
https://g-desoutter.github.io/kbofthemonth/kbs.json
```

```json
{
  "generated_at": "2026-08-14T19:28:40.727955+00:00",
  "month": "2026-Aug",
  "kbs": {
    "Microsoft .NET Framework 3.5 AND 4.8 on Windows Server 2022": ["KB5120705"],
    "Windows Server 2016": ["KB5094122", "KB5120418"],
    "Windows Server 2019": ["KB5094123", "KB5120238"],
    "Windows Server 2022": ["KB5120242", "KB5123303"]
  }
}
```

| Champ | Description |
|---|---|
| `generated_at` | Horodatage UTC ISO 8601 de la génération |
| `month` | Mois du document CVRF source (`AAAA-Mmm`) |
| `kbs` | Nom complet du produit → liste triée des KB, préfixées `KB` |

Les clés produit reprennent les libellés exacts du MSRC : outre les éditions
Windows Server, on y trouve les déclinaisons .NET Framework, qui font l'objet
de correctifs distincts.

## Utilisation

**PowerShell**

```powershell
$catalog = Invoke-RestMethod 'https://g-desoutter.github.io/kbofthemonth/kbs.json'
$catalog.kbs.'Windows Server 2022'
```

**Python**

```python
import requests

catalog = requests.get(
    "https://g-desoutter.github.io/kbofthemonth/kbs.json", timeout=30
).json()
print(catalog["month"], catalog["kbs"]["Windows Server 2025"])
```

**curl + jq**

```bash
curl -s https://g-desoutter.github.io/kbofthemonth/kbs.json \
  | jq -r '.kbs["Windows Server 2019"][]'
```

## Fonctionnement

```
API MSRC — cvrf/v3.0/cvrf/{AAAA-Mmm}
  │
  ├─ Filtrage produits     Windows Server 2016/2019/2022/2025, hors Server Core
  ├─ Filtrage remédiations Type=2 (mise à jour de sécurité), hors Hotpatch
  ├─ Sortie déterministe   produits et KB triés, dédoublonnés
  │
  ├─→ docs/kbs.json        commité uniquement si le contenu change
  └─→ GitHub Pages         endpoint public + interface de consultation
```

Le workflow s'exécute chaque **mercredi à 12h00 UTC**, au lendemain du Patch
Tuesday, et reste déclenchable à la main depuis l'onglet Actions.

Deux garde-fous notables. Si le document CVRF du mois courant n'est pas encore
publié — cas du premier mercredi du mois — le script bascule sur le mois
précédent plutôt que d'échouer. Et si les KB extraites sont identiques à celles
déjà publiées, le fichier n'est pas réécrit : aucun commit parasite, et
l'historique ne contient que de vrais changements.

## Développement

```bash
git clone https://github.com/g-desoutter/kbofthemonth.git
cd kbofthemonth
pip install -r requirements.txt

python main.py                      # régénère docs/kbs.json
python -m http.server -d docs 8000  # prévisualise la page sur localhost:8000
```

Le script écrit ses diagnostics sur `stderr` et renvoie un code de sortie non
nul si le document est indisponible, vide, ou ne contient aucun produit
correspondant — de quoi faire échouer le job franchement plutôt que de publier
un catalogue tronqué.

## Stack

Python 3.12 · GitHub Actions · GitHub Pages · [API MSRC](https://api.msrc.microsoft.com)

## Limites

Les données sont fournies telles qu'extraites du MSRC, sans validation
indépendante. Une même KB peut apparaître sous plusieurs libellés produit
lorsque Microsoft l'associe à plusieurs ProductID. Ce projet n'est ni affilié
ni approuvé par Microsoft.

## Licence

MIT — voir [LICENSE](LICENSE).
