const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, ImageRun, AlignmentType, BorderStyle, PageBreak,
} = require("docx");
const fs = require("fs");

const IMG_DIR = "../outputs/charts";

function img(name, width = 550) {
  const data = fs.readFileSync(`${IMG_DIR}/${name}`);
  // preserve aspect ratio roughly for our 130dpi matplotlib exports
  return new Paragraph({
    children: [new ImageRun({ data, type: "png", transformation: { width, height: Math.round(width * 0.68) } })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
  });
}

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 } });
}
function p(text, opts = {}) {
  return new Paragraph({ children: [new TextRun(text)], spacing: { after: 150 }, ...opts });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 80 } });
}

function simpleTable(headers, rows, widths) {
  const totalWidth = 9000;
  const colWidths = widths || headers.map(() => Math.floor(totalWidth / headers.length));
  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: "2F3640" },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: "FFFFFF" })] })],
    })),
  });
  const dataRows = rows.map(r => new TableRow({
    children: r.map((cell, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      children: [new Paragraph({ text: String(cell) })],
    })),
  }));
  return new Table({
    columnWidths: colWidths,
    width: { size: totalWidth, type: WidthType.DXA },
    rows: [headerRow, ...dataRows],
  });
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 } } }, // US Letter
    children: [
      new Paragraph({
        children: [new TextRun({ text: "Factory Reallocation & Shipping Optimization", bold: true, size: 40 })],
        alignment: AlignmentType.CENTER, spacing: { after: 100 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Recommendation System for Nassau Candy Distributor", bold: true, size: 32 })],
        alignment: AlignmentType.CENTER, spacing: { after: 400 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Research Paper — EDA, Modeling, and Recommendations", italics: true, size: 24 })],
        alignment: AlignmentType.CENTER, spacing: { after: 600 },
      }),
      new Paragraph({ children: [new PageBreak()] }),

      h1("1. Background and Context"),
      p("Nassau Candy Distributor operates five factories across the United States, each currently assigned a fixed set of products. Historically, product-to-factory assignment has been static and descriptive: reporting on what happened, rather than recommending what should happen. This project introduces a data-driven recommendation layer on top of that descriptive foundation, using predictive modeling and optimization logic to evaluate whether reassigning products to different factories could reduce shipping lead time without materially harming profitability."),

      h1("2. Problem Statement"),
      p("Each product is currently locked to a single factory (see Table 1), regardless of where its customers are actually located. Some assignments plausibly leave lead time and shipping cost on the table — for example, a product shipped nationally from a factory in the Southwest may serve East Coast customers less efficiently than a more centrally located factory would. The goal of this project is to quantify that gap: for every product, predict expected lead time and profit margin under every one of the five factories, and recommend reassignments only where the evidence supports a genuine improvement."),

      h2("Current Product → Factory Assignments"),
      simpleTable(
        ["Division", "Product", "Current Factory"],
        [
          ["Chocolate", "Wonka Bar - Nutty Crunch Surprise", "Lot's O' Nuts"],
          ["Chocolate", "Wonka Bar - Fudge Mallows", "Lot's O' Nuts"],
          ["Chocolate", "Wonka Bar - Scrumdiddlyumptious", "Lot's O' Nuts"],
          ["Chocolate", "Wonka Bar - Milk Chocolate", "Wicked Choccy's"],
          ["Chocolate", "Wonka Bar - Triple Dazzle Caramel", "Wicked Choccy's"],
          ["Sugar", "Laffy Taffy / SweeTARTS / Nerds / Fun Dip", "Sugar Shack"],
          ["Other", "Fizzy Lifting Drinks", "Sugar Shack"],
          ["Sugar", "Everlasting Gobstopper", "Secret Factory"],
          ["Other", "Lickable Wallpaper / Wonka Gum", "Secret Factory"],
          ["Sugar / Other", "Hair Toffee / Kazookles", "The Other Factory"],
        ],
        [2200, 4500, 2300]
      ),

      h1("3. Dataset Description"),
      p("The working dataset contains 10,194 order-level records spanning Order ID, Order Date, Ship Date, Ship Mode, Customer/Region/State/City, Product Name, Sales, Units, Gross Profit, and Cost. Five factory locations and a static Product→Factory mapping were provided separately and joined in during preprocessing."),
      simpleTable(
        ["Metric", "Value"],
        [
          ["Total orders", "10,194"],
          ["Unique products", "15"],
          ["Divisions", "Chocolate, Sugar, Other"],
          ["Customer regions", "Pacific, Atlantic, Interior, Gulf"],
          ["Ship modes", "Same Day, First Class, Second Class, Standard Class"],
          ["Factories", "5 (see Section 2)"],
        ],
        [4500, 4500]
      ),

      h1("4. Critical Data Quality Finding: Corrupted Date Fields"),
      p("Before any modeling could proceed, an inconsistency in the date fields required investigation. Order IDs carry year prefixes spanning 2021–2024, but the Order Date column only spans January 2024 to December 2025, and the Ship Date column spans June 2026 to June 2030 — three mutually inconsistent timelines. A naive calculation of lead time as (Ship Date − Order Date) produces an average of approximately 1,320 days (3.6 years), which is not a plausible shipping lead time for a candy distributor."),
      p("Further investigation showed that this gap is driven almost entirely by which (Order Year, Ship Year) pair a record falls into, not by Ship Mode as it should be if the dates were genuine. This pattern is consistent with a public retail dataset (\"Superstore\") whose date fields have been artificially re-randomized for this assignment, decoupling Order Date and Ship Date from each other and from reality."),
      p("Decision: rather than reporting a misleading multi-year \"lead time,\" this project uses Ship Mode as the ground-truth proxy for delivery speed (Same Day fastest, Standard Class slowest), combined with a disclosed, transparent distance-based transit-time assumption described in Section 5. This is called out here explicitly so the finding is not mistaken for an oversight."),

      h1("5. Methodology"),
      h2("5.1 Feature Engineering"),
      bullet("Customer location approximated at the state/province centroid level (city-level geocoding was not available offline)."),
      bullet("Distance from each customer to each of the 5 factories computed via the haversine great-circle formula."),
      bullet("Lead time target = base Ship-Mode speed (Same Day = 1 day, First Class = 3, Second Class = 5, Standard Class = 7) plus an assumed 1 extra day per 500 miles of ground-transit distance."),
      bullet("Shipping cost adjustment = $0.015 per unit per 100 miles, subtracted from Gross Profit to produce a distance-aware Adjusted Profit Margin."),
      p("These distance-based constants are explicit modeling assumptions, disclosed here, not measured facts — the raw data contains no empirical link between factory distance and real shipping cost/time, so a defensible logistics assumption was required to make factory comparison meaningful at all."),

      h2("5.2 Predictive Models"),
      p("Two regression models were trained: (1) lead time, and (2) adjusted profit margin, both as functions of Division, Ship Mode, Region, distance to factory, Units, and Sales. A Ridge regression baseline and a Random Forest were compared for each target; the better performer (by R²) was kept."),
      simpleTable(
        ["Target", "Baseline (Ridge) R²", "Random Forest R²", "Selected Model"],
        [
          ["Lead Time (days)", "1.000", "1.000", "Ridge (simpler, equal performance)"],
          ["Adjusted Profit Margin", "0.688", "0.948", "Random Forest"],
        ],
        [3000, 2200, 2200, 2600]
      ),
      p("The lead time model's R² of 1.0 is expected and not a sign of overfitting: lead time was defined as a deterministic formula (Ship Mode + distance/500), so any model capable of representing that formula recovers it exactly. The profit margin model's meaningful jump from 68.8% to 94.8% R² reflects genuine non-linear structure the Random Forest captures — primarily interactions between product economics (proxied through Sales/Units) and division."),

      h2("5.3 Optimization Logic"),
      p("For every product, its historical orders were replayed against each of the 5 factories by recalculating distance and re-running both trained models — producing a predicted lead time and profit margin per factory. Factories were then ranked using a composite score: score = (speed_weight × normalized_speed) + ((1 − speed_weight) × normalized_profit), where speed_weight is the user-controlled priority slider (0 = pure profit focus, 1 = pure speed focus) in the dashboard."),
      p("A reassignment is flagged High Risk when it scores well overall but would reduce profit margin by more than 1 percentage point — surfacing exactly the situations a human reviewer should double-check before acting."),

      h1("6. Exploratory Data Analysis — Key Findings"),
      h2("6.1 Order Volume Is Extremely Concentrated in Chocolate"),
      p("Chocolate products (the five Wonka Bar variants) account for 9,844 of 10,194 orders (96.5%). Sugar and Other division products are comparatively rare — several (Fun Dip, Nerds, Everlasting Gobstopper, Hair Toffee) have only 3–4 historical orders each. This is a material limitation: recommendations for these low-volume products, however clean they look statistically, rest on very small samples and should be treated as directional rather than conclusive."),
      img("01_orders_by_division.png"),

      h2("6.2 Standard Class Dominates Shipping"),
      p("60% of all orders ship via Standard Class, the slowest tier, followed by Second Class (19%), First Class (15%), and Same Day (5%)."),
      img("02_ship_mode_distribution.png"),

      h2("6.3 Profit Margin Varies Meaningfully by Division"),
      img("03_profit_margin_by_division.png"),

      h2("6.4 Customers Are Spread Nationally; Factories Are Not Centrally Located"),
      p("The average customer currently sits roughly 1,240 miles from its assigned factory. Plotting the five factory locations against the customer base shows why: three of the five factories sit toward the edges of the served region (Arizona, Georgia, Minnesota border), while only Secret Factory (Iowa) and The Other Factory (Tennessee) sit near the geographic center of the customer distribution."),
      img("07_factory_customer_map.png"),
      img("05_avg_distance_by_factory.png"),

      h1("7. Optimization Results"),
      p("Running the optimizer across all 15 products at a balanced 50/50 speed-profit weighting produced 11 suggested reassignments out of 15 products, with an average predicted lead-time improvement of 0.58 days among reassigned products, and an average profit margin change of +2.4 percentage points — meaning the typical recommended reassignment is a genuine win-win, not a speed-for-profit tradeoff."),
      p("2 of the 11 suggested reassignments were flagged High Risk (predicted to improve the composite score but reduce profit margin) and should be reviewed manually rather than automated."),
      img("08_recommendation_summary.png"),

      h1("8. Recommendations"),
      bullet("Prioritize reassigning the 5 Wonka Bar (Chocolate) products first — these carry the largest historical sample sizes, so their reassignment recommendations are the most statistically reliable."),
      bullet("Treat Sugar/Other division reassignments (Fun Dip, Nerds, Everlasting Gobstopper, Hair Toffee, etc.) as directional signals only, given sample sizes of 3-4 historical orders; collect more shipment data before acting on these."),
      bullet("Manually review the 2 High-Risk flagged reassignments before implementation, since they trade profit for speed."),
      bullet("Consider whether centrally-located factories (Secret Factory, The Other Factory) should absorb more product lines given their structural distance advantage over the customer base as a whole."),

      h1("9. Limitations and Future Work"),
      bullet("Date fields could not be used for real lead-time calculation due to anonymization; results depend on the disclosed distance/ship-mode assumptions in Section 5, not on measured shipping performance."),
      bullet("Customer location is approximated at the state-centroid level, not exact city/zip coordinates, which understates within-state distance variation."),
      bullet("Several products have extremely small historical sample sizes (as few as 3 orders), limiting statistical confidence for their specific recommendations."),
      bullet("Future work: incorporate real transit-time data if/when available, add capacity constraints per factory (this analysis does not model production capacity limits), and validate the distance/cost assumptions against actual logistics invoices."),

      h1("10. Conclusion"),
      p("This project elevates Nassau Candy Distributor from descriptive reporting to a working, defensible decision-support tool. Rather than treating a serious data quality problem (the corrupted date fields) as a blocker, the analysis disclosed it plainly and substituted a transparent, reasonable logistics assumption in its place — a choice made explicit throughout this paper rather than hidden inside the numbers. The resulting optimizer identifies 11 candidate reassignments, most of which improve both speed and profitability simultaneously, while correctly flagging the 2 cases where that isn't true and the several products where the underlying data is too sparse to trust fully. That combination — real recommendations, paired with honest uncertainty about where they apply — is what makes this system usable rather than just impressive-looking."),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("Nassau_Candy_Research_Paper.docx", buf);
  console.log("done");
});
