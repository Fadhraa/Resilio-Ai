# ResilioAI Design Direction (DESIGN.md)

> **Antislop Design Read:**
> Reading this as: *Mission-Critical Food Logistics & Emergency Mitigation Command Dashboard for SPPG Operations and BGN Regulatory Auditing, in an authoritative institutional command-center visual language, dial ENERGY 2 / RHYTHM 2 / MOTION 1.*

---

## 1. Brand Identity & Character
- **Product Name:** ResilioAI Engine (SPPG Command & Control)
- **Sector:** National Nutrition Program (Program Makan Bergizi Gratis 2026 - BGN / SPPG Wilayah I)
- **Role:** High-stakes operational resilience platform preventing food supply failures, cold-chain spoilage, and regulatory non-compliance.
- **Personality:** Authoritative, transparent, highly reliable, calm under pressure, rigorously auditable (Zero Hallucination).

---

## 2. Anti-Slop Liveliness Dials
- **ENERGY: 2 (Balanced)**
  - Neither a generic sterile grey box nor a flashy neon consumer app. Serious institutional enterprise tool with crisp contrast and clear visual gravity.
- **RHYTHM: 2 (Structured with deliberate focal points)**
  - Clear hierarchy: Emergency Status Header -> Dual Workspace (Conversational Copilot + Real-Time Mitigation Pipeline) -> Data Grid & Actionable Verification.
- **MOTION: 1 (Calm & Purposeful)**
  - Hover highlights, smooth tab switches, step progress indicators. Strictly no gimmicky bounce, float, or random fade-in loops. Respects `prefers-reduced-motion`.

---

## 3. Color System & Contrast (WCAG AA Certified)
- **Dominant Surfaces:**
  - Base Background: `#f8fafc` (Slate 50)
  - Card/Panel Background: `#ffffff` (Pure White)
  - Panel Borders: `#e2e8f0` (Slate 200)
- **Brand & Hierarchy:**
  - Primary Text & Headings: `#0f172a` (Slate 900) - Maximum readability
  - Secondary Text & Metadata: `#475569` (Slate 600)
  - Muted Borders & Dividers: `#cbd5e1` (Slate 300)
- **Functional Semantics (Zero Slop - Every Color Has a Job):**
  - **Institutional Blue (`#1e40af` / `#2563eb`):** Primary identity, SPPG verification badge, active step indicator.
  - **Compliance Green (`#059669` / `#10b981`):** Certified Halal (UU 33/2014 valid), SOP ceiling passed, PO issued.
  - **Alert Amber (`#d97706` / `#f59e0b`):** Supply bottleneck, freezer space constrained, approval required.
  - **Disruption Crimson (`#dc2626` / `#ef4444`):** Active supplier failure, delivery canceled, deficit alert.

---

## 4. Typography & Data Presentation
- **Primary Typeface:** Geist Sans / Inter (`font-sans`) - Clear, authoritative, highly legible at small sizes (11px-14px).
- **Tabular Figures & Codes:** Geist Mono (`font-mono`) - Reserved strictly for ID codes (`ITEM-AYAM-01`, `SUP-ALT-02`), timestamps, currency figures (Rupiah), and kilogram metrics for visual scanning alignment.
- **Tone of Voice (Copywriting):**
  - Strictly **NO generic AI buzzwords** ("Next Generation", "Revolutionary", "AI Powered").
  - Strictly **NO em dashes (`—`)**; use colon, commas, or parentheses instead.
  - Authentic Indonesian operational terminology for SPPG officers (*"Kepala SPPG"*, *"Kapasitas Ruang Pendingin (Freezer)"*, *"Pagu Anggaran SOP BGN"*, *"Penerbitan Surat Pesanan (PO) Resmi"*).

---

## 5. Information Architecture & Key Interactive Zones
1. **Top Institutional Bar:** SPPG Wilayah I header, live system status, current time, and quick action bar.
2. **Zone A: Live Interactive AI Copilot (Chat Panel):**
   - Direct conversational interaction with the backend `/api/v1/chat` agent.
   - Handles natural questions, supplier inquiries, incident reports, and conversational CRUD.
3. **Zone B: Real-Time Mitigation Visualizer (LangGraph Pipeline):**
   - 5-step transparent workflow visualizer.
   - Shows exact mathematical deficit calculations and Split Delivery rationale.
4. **Zone C: Operational Inventory & Supplier Master Data:**
   - Active stock vs safety threshold, freezer remaining space.
   - Verified supplier registry with Halal status and SOP price comparison.
5. **Zone D: Human-in-the-Loop Gatekeeper Modal:**
   - Actionable preview data card with one-click authorization or modification.
