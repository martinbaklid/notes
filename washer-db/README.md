# Washer database: parts-checked model variants

The parts check behind the Google Sheet "Washing machines" (tabs `db_models`, `db_matches`,
`db_key_parts`, `Shop listings`). Everything here was collected on 9 Nov 2026.

## Question it answers

Shops sell the same machine under different model codes. For example, Bosch WGG244ZISN
(Skousen) and WGG244ZTSN (Elkjøp) are the same machine. Energy-label values alone cannot show
this: 42 of the 63 Overview models share all four label values (kg, rpm, kWh/100 cycles,
spin dB) with another Overview model. So each candidate pair is checked against the
manufacturer's own spare-parts list.

## Method

1. **Candidates.** Every Bosch, Siemens, Miele and AEG washer and washer-dryer listed at
   Elkjøp (public product sitemap) and Power (public product-list API) is compared with the
   63 Overview models. A shop code becomes a candidate for an Overview model of the same brand
   and type (washer or washer-dryer) when the energy-label values match, or when the model code
   shares a base (see `scripts/fam.py`). This gives 66 candidate codes and 117 pairs.
2. **Parts lists.** For every candidate and every Overview model, the full spare-parts list
   is read from the manufacturer's public catalogue, without logging in or using a cart:
   - Bosch and Siemens: BSH spare-parts shop. Lookup key: E-Nr, the newest variant for that
     exact code (`scripts/bsh_bom.js`).
   - AEG: shop.aeg.no. Lookup key: PNC, taken from Power's product data or from the PNC
     shown on aeg.no / aeg.se (`scripts/aeg_bom.js`, `scripts/aeg_pnc2.js`).
   - Miele: Miele's spare-parts catalogue (MSD). Lookup key: the device for that exact type
     code, WCS/WPS/WPM variant (`scripts/miele_bom.js`).
3. **Comparison** (`scripts/build_db.py`):
   - Mechanical subset:
     - BSH: positions 03xx (oscillating system).
     - AEG: section "Funksjonelle deler" plus the motor.
     - Miele: function groups 040 (suds container, dampers) and 130 (motor).
   - Key parts: outer tub, motor, shock absorbers and drum, found by name and position. See
     `db_key_parts.csv`.
   - Verdict:
     - **Same mechanics (parts verified):** same outer tub, same motor, and at least 80 % of
       the mechanical parts in common.
     - **Same platform, outer tub part number differs:** different tub part number, but at
       least 75 % of the mechanical parts in common. This is often a newer tub revision.
     - **Same platform, some mechanical parts differ:** 50–80 % of the mechanical parts in
       common.
     - **Different machine:** outer tub or motor differs, or less than 50 % of the mechanical
       parts in common.
     - **Parts not checked:** no parts list found, or the parts list is missing its
       mechanical section.
   - Features (auto-dosing, steam, Wi-Fi) are compared separately. Same mechanics can still
     mean different features.

## Limits

- **Weight is not used.** Weights come from different sources (manufacturer vs. shop), so
  they would give false differences.
- **Inconsistent steam data.** "Steam" differences are often a source inconsistency. The
  brand tabs count Bosch "Iron Assist" as steam, while Elkjøp's spec table often says
  "Dampfunksjon: Nei" for the same machine.
- **Power gives no features.** Power lists no feature data, so for Power-only codes the
  features are "Not listed".
- **Not every E-Nr variant is compared.** BSH codes have several E-Nr variants (production
  series). The newest one with a parts list is used, so an older series may differ.
- **Missing AEG parts lists:**
  - shop.aeg.no gives no parts list for LR622O94Q, LR734E94EQ or LR734W16Q.
  - No PNC was found for LWR724P16P.
  - LWR732C96Q's list has no "Funksjonelle deler" section.
- **Komplett is not included.** komplett.no refused connections from the collection
  environment.

## Files

| File | Contents |
|---|---|
| `db_models.csv` | one row per model code: specs, features, catalogue, lookup key, parts-list status |
| `db_matches.csv` | one row per Overview model × candidate: tub, motor, overlap, verdict, feature differences |
| `db_key_parts.csv` | key parts per model (tub, motor, dampers, drum) with part number and catalogue price |
| `parts/<code>.csv` | full parts list per model, with a `mechanical_subset` flag |
| `raw/` | raw JSON as read from the catalogues and shops, for re-checking |
| `scripts/` | collection and comparison scripts as they were run (paths point at the original workspace) |
