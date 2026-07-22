const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, ImageRun, AlignmentType, PageBreak,
} = require("docx");
const fs = require("fs");

const IMG_DIR = "../outputs/charts";
function img(name, width = 500) {
  const data = fs.readFileSync(`${IMG_DIR}/${name}`);
  return new Paragraph({
    children: [new ImageRun({ data, type: "png", transformation: { width, height: Math.round(width * 0.68) } })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
  });
}
function h1(text) { return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 250, after: 120 } }); }
function p(text) { return new Paragraph({ children: [new TextRun(text)], spacing: { after: 150 } }); }
function bullet(text) { return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 80 } }); }

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
  return new Table({ columnWidths: colWidths, width: { size: totalWidth, type: WidthType.DXA }, rows: [headerRow, ...dataRows] });
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 } } },
    children: [
      new Paragraph({
        children: [new TextRun({ text: "Executive Summary", bold: true, size: 40 })],
        alignment: AlignmentType.CENTER, spacing: { after: 100 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Factory Reallocation & Shipping Optimization — Nassau Candy Distributor", bold: true, size: 26 })],
        alignment: AlignmentType.CENTER, spacing: { after: 400 },
      }),

      h1("The Problem"),
      p("Nassau Candy Distributor ships products from five factories to customers nationwide. Each product is currently locked to one factory, regardless of where its customers actually are. This can mean longer delivery times and higher shipping costs than necessary."),

      h1("What We Did"),
      p("We analyzed 10,194 historical orders and built a tool that predicts, for every product, what delivery speed and profit margin would look like if it were made at any of the five factories — not just the one it's currently assigned to. The tool then recommends reassignments only where the data supports a genuine improvement."),

      h1("What We Found"),
      bullet("11 of the 15 products could benefit from being reassigned to a different factory."),
      bullet("On average, reassigned products would ship 0.58 days faster while ALSO improving profit margin by 2.4 percentage points — a win-win, not a tradeoff."),
      bullet("2 of those 11 reassignments are flagged as higher-risk: faster shipping, but at some cost to profit. These need a manual decision, not automatic action."),
      bullet("Factories located closer to the geographic center of the customer base (Iowa, Tennessee) consistently outperform factories at the edges of the service area (Arizona, Georgia, Minnesota)."),

      img("08_recommendation_summary.png"),

      h1("An Important Caveat"),
      p("Some products (like Fun Dip, Nerds, and Everlasting Gobstopper) have very few historical orders — as few as 3. Their recommendations point in a reasonable direction but shouldn't be treated as final until more data is collected. The 5 chocolate bar products, by contrast, each have over 1,800 historical orders and their recommendations are statistically solid."),

      h1("Recommended Next Steps"),
      bullet("Act first on the high-volume, high-confidence recommendations (the 5 chocolate bar products)."),
      bullet("Manually review the 2 flagged high-risk reassignments before implementing."),
      bullet("Continue collecting shipment data on low-volume products before reassigning them."),
      bullet("Use the accompanying interactive dashboard to explore any product, region, or priority setting directly."),

      h1("Bottom Line"),
      p("This project turns Nassau Candy's shipping data into a practical decision-making tool. The recommendations are conservative by design — they flag risk and low-confidence cases rather than hiding them — so leadership can act on the clear wins immediately while treating the uncertain cases with appropriate caution."),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("Nassau_Candy_Executive_Summary.docx", buf);
  console.log("done");
});
