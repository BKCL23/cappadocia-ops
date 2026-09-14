# KDP Paperback Publishing Guide

You've already got the Kindle ebook. A paperback is a **separate format** on the same KDP book record — a second royalty stream, and physical copies you can sell or display at your hotel's front desk. Here's how to publish it.

**Files to upload (in this folder):**
- Interior: **`Cappadocia-Paperback-Interior.pdf`**
- Cover: **`Cappadocia-Paperback-Cover.pdf`**

---

## The exact settings (match these — the files are built for them)

In KDP, open your book and click **"Create Paperback"** (or start a new paperback), then:

| Setting | Choose | Why |
|---|---|---|
| **ISBN** | Get a **free KDP ISBN** | Free; required for paperback. (Don't reuse the ebook's ASIN.) |
| **Trim size** | **5.5 × 8.5 in** | The interior + cover are built to this exact size. |
| **Bleed** | **No bleed** | The interior is text-only with margins — not full-bleed. |
| **Paper type** | **Black & white interior, white paper** | The spine width in the cover was calculated for **white** paper. If you pick cream, the spine changes — see below. |
| **Cover finish** | **Matte** | Reads as premium for a travel guide (glossy is fine too). |

Then upload the two PDFs, open KDP's **Print Previewer**, and check it end to end. The previewer flags anything outside the printable area.

> **Page count = 32.** Spine width was computed as **~0.072 in** for 32 pages on white paper. KDP does not allow spine **text** under 100 pages, so the spine is intentionally blank. That's normal for a slim guide.

---

## If the page count or paper ever changes

The cover's spine width is tied to the exact page count and paper. If KDP reports a different page count, or you choose **cream** paper, **regenerate the cover**:

```bash
# (installs: pip install reportlab pillow)
python3 build-paperback-cover.py <PAGE_COUNT>
```

For cream paper, change `PPI_WHITE = 0.002252` to `0.0025` in `build-paperback-cover.py` and rerun. Then re-upload `Cappadocia-Paperback-Cover.pdf`.

To regenerate the interior (e.g. after edits): `python3 build-paperback-interior.py` — it prints the new `PAGES=` count, which you feed to the cover command above.

---

## The barcode

Leave it to KDP. The back cover has a deliberately **clear bottom-right area** — KDP prints the ISBN barcode there automatically. Don't add your own.

---

## Pricing (this is different from ebook — printing costs money)

Paperback royalty = **60% of your list price − the printing cost**. For a ~32-page black-and-white 5.5×8.5 book, the printing cost is low (roughly a couple of dollars; KDP shows you the exact figure).

- **List at $8.99–$9.99.** Example at $9.99: 60% = ~$6.00, minus ~$2.30 printing ≈ **~$3.70 royalty** per copy (KDP shows your real numbers before you publish).
- KDP will warn you if your price is below the minimum that covers printing — just raise it until the royalty is positive.
- Set the US price; KDP suggests prices for other marketplaces.

---

## After you publish

1. **Order an author proof copy** (KDP offers author copies near printing cost) so you can hold it, check it, and put one on your hotel's front desk.
2. **Sell/display at the hotel.** A physical guide by the owner, at reception, is a lovely touch — and an easy upsell.
3. **Link the paperback and ebook** — KDP shows them together on one Amazon listing, so a paperback review helps the ebook and vice versa.
4. Use the same **launch content** (`launch-content.md`) — just mention "now in paperback too."

---

## Want a thicker book?

A 32-page guide is a legit slim paperback, but if you'd like a more substantial book (100+ pages → spine text becomes possible, more shelf presence), I can **expand the content**: deeper chapters, more day-by-day detail, an expanded restaurant/operator section, maps, and a phrasebook appendix. Just ask.

---

*Interior source: `build-paperback-interior.py` · Cover source: `build-paperback-cover.py` · Full-res cover image: `cover-full.png`*
