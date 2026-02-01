# Laser Cutting Workflow (Test Sample)

**Goal:** Calibrate laser settings to achieve a "stepped" terrain effect on 3mm MDF without excessive charring, ensuring the 1:5,533 scale details (0.45mm alleys) are visible.

## 1. Material Preparation
*   **Material:** 3mm MDF or 1/8" Balsa.
*   **Masking:** Apply wide painter's tape (white tape) to the *top* surface. This prevents smoke stains on the high points (roofs).
    *   *Note:* For 3D engraving, masking can sometimes interfere with depth perception or melt into the debris. If the tape burns poorly, try air-assist ON with no tape for the second run.

## 2. Image Processing
**Supported Formats:** BMP, JPG, PNG, SVG, G-code.
*We use **PNG** for this heightmap workflow as it supports high-resolution grayscale needed for the embossing effect.*

**Physical Size:** 2cm x 2cm (20mm x 20mm).
*Ensure you scale the image to these exact dimensions in your laser software to maintain the 1:5,533 scale.*

### Option A: LaserPecker Design Space (Recommended)
*   **Mode:** Select **"2D Embossing Effect"** (or sometimes called "Relief").
*   **Invert:** Ensure the software interprets **White** as "High/No Burn" and **Black** as "Deep/Max Burn". 
    *   *Verification:* Our image has Roofs=White (255) and Streets=Dark (20). This matches the standard behavior where lighter areas burn less.

### Option B: LightBurn / LaserGRBL (Generic)
*   **Mode:** **Grayscale** / **3D Slice** (not Dither/Jarvis).
*   **Invert:** Ensure **Black = High Power (Deep)** and **White = Low Power (Surface)**.

## 3. Recommended Settings (LaserPecker 5W Specific)
*Based on available controls: Resolution, Pass, Power, Depth.*

| Parameter | Setting | Reason |
| Parameter | Setting | Reason |
| :--- | :--- | :--- |
| **Resolution** | **1.3K** | Proven best for MDF to avoid over-charring. |
| **Power** | **100%** | Max intensity. |
| **Depth** | **20 - 25%** | increased from 15% to get better relief. |
| **Passes** | **3 - 4** | Multiple passes needed to erode material. |

*Note: If "Depth" is too low (not cutting deep enough), increase Passes first, then increase Depth.*

### **First Run Recommendation**
Use these exact settings for your first test to minimize risk of charring:
*   **Resolution:** 2K
*   **Power:** 100%
*   **Depth:** 15%
*   **Passes:** 3

### **Test 2 Recommendation (If Test 1 Failed)**
If Test 1 failed to penetrate (e.g., masking tape wasn't cut through):
1.  **Remove Masking Tape:** Tape can reflect diode lasers or absorb too much power.
2.  **Settings:** Keep same settings (Res 2K, Power 100%, Runs 3).
3.  **Observation:** Check if it now engraves the MDF.
    *   *If yes:* The tape was the issue.
    *   *If no:* We need to increase **Depth** to 20-30% or add more passes.

## 4. The "Mohenjo-daro Test"
1.  **Focus:** Focus on the *surface* of the board (on top of tape if using it, or board if not).
2.  **Burn:** Run the job.
3.  **Clean:** Scrub with a soft toothbrush and IPA/Water.
4.  **Inspect:**
    *   **Alleys (0.45mm):** Are they visible or just a scorched blur?
    *   **Poor Homes (1mm mounds):** Do they look like distinct bumps or flat noise?
### **Test 3 settings (User Refinement)**
*Findings from Test 2: "Needle" char structures formed but correct terrain was underneath. Scrubbing is required.*

**Settings:**
*   **Resolution:** **1.3K** (Reduced from 2K to reduce line overlap/charring).
*   **Power:** 100%
*   **Depth:** 15%
*   **Passes:** 3 (Maintained high energy to ensure depth).

### **Test 4 Recommendation (Finalizing Depth)**
*Refinement from Test 3: 1.3K was clean but shallow.*

**Adjustments:**
1.  **Keep Resolution at 1.3K** (This fixed the charring).
2.  **Increase Depth to 20% - 25%** (To dig deeper).
3.  **Passes:** Keep at 3-4.

*Target:* We want the streets to be distinct channels (approx 0.5 - 1mm deep) while keeping the roofs flat.

### **Test 5 Recommendation (EVA Foam)**
**Safety Warning:** EVA foam releases fumes when heated. **Good ventilation is MANDATORY.**
*   **Material:** High-Density EVA Foam (e.g., Cosplay foam).
*   **Behavior:** It **MELT-VAPORIZES** rather than burning. Heat management is critical to prevent "gooey" edges.

**Proposed Settings (Start Fast):**
*   **Resolution:** **1.3K** or **1K** (Lower res helps prevent heat buildup).
*   **Power:** **100%**
*   **Speed:** **Increase Speed** (Try 1500 - 2000 mm/min if possible, or lower Depth).
*   **Depth:** **10 - 15%** (Start shallow. Foam cuts much easier than wood).
*   **Passes:** **1 - 2**.
*   **Invert:** Same logic (ensure Roofs are unburnt).

*Tip:* If edges curl or melt, **Increase Speed** or **Decrease Density/LPI**.

## 6. FAQ: Why PNG and not G-code?
*   **G-code:** typically used for **Vector** paths (Cut/Score). It moves the laser along lines. It's binary (laser ON/OFF) or constant power. Hard to do smooth "slopes" or 3D terrain.
*   **PNG (Raster):** We use **Grayscale Rasterizing**. The laser scans back and forth like a printer. The software dynamically changes laser power *per pixel* based on brightness (Black=100%, Gray=50%, White=0%). This is the only easy way to get "3D" embossing.

## 7. Troubleshooting: Uneven Surface (Balsa Wood Grain)
If you see ridges or uneven depths despite correct settings, it is likely the **variable density** of Balsa wood fibers. The laser burns soft pith faster than hard grain.

**Solutions:**
1.  **Switch to MDF (Highly Recommended):** MDF (Medium Density Fiberboard) is engineered to be perfectly uniform. It is the standard for laser relief maps.
2.  **Cross-Hatching (If using Balsa):**
    *   Rotate the piece 90 degrees between passes (if possible) so the laser grain cuts across the wood grain.
## 8. Final Verified Settings (The "Golden" Recipe)
**Material:** EVA Foam
**Strategy:** Block City (Black & White Raster)

| Parameter | Setting | Notes |
| :--- | :--- | :--- |
| **Material** | **EVA Foam** | High density. |
| **File Type** | **PNG (Block)** | `mohenjo_test_sample_block.png` (Black/White only). |
| **Resolution** | **1.3K** | Optimal detail without melting. |
| **Power** | **100%** | |
| **Depth** | **5%** | Crisp, clean depth. |
| **Passes** | **1** | Fast production. |
| **Preparation**| **None** | No tape. |

### **Alternative: Verified Balsa Settings**
**Material:** Balsa Wood (4x4cm Block)
**Strategy:** Block City (Black & White)

| Parameter | Setting | Notes |
| :--- | :--- | :--- |
| **Resolution** | **1.3K** | Higher res than EVA for wood detail. |
| **Power** | **100%** | |
| **Depth** | **25%** | Deeper burn required for wood. |
| **Passes** | **1** | |
| **Note** | Optimal for **40mm x 40mm** size. | Larger blocks may need different settings. |

> [!IMPORTANT]
> **Size Matters:** 5x5cm blocks and 6x6cm blocks require **different settings** (likely due to heat dissipation). You must re-calibrate if you change the total surface area significantly.

## 9. Alternative Strategies (Streets Only)
*If you want to carve ONLY the streets and guarantee untouched rooftops.*

### **Option A: Block City (Raster)**
*   **File:** `mohenjo_test_sample_block.png`
*   **Concept:** Only Streets are Black (100% Power). Everything else is White (0% Power).
*   **Settings:** Use "EVA Foam" settings (1.3K, 15% Depth).
*   **Benefit:** Zero chance of "haze" on roofs. Flat look (no courtyard depth).

### **Option B: Vector Cut (SVG)**
*   **File:** `mohenjo_test_sample.svg`
*   **Concept:** Laser follows the vector path.
*   **Mode:** **Fill** (or "Deep Cut" if you just want lines).
*   **Settings:** 
    *   **Fill:** Power 100%, Speed 2000 mm/min.
    *   **Score/Cut:** Power 40%, Speed 1000 mm/min (for simple lines).
