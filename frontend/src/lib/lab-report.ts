import { jsPDF } from "jspdf";
import { autoTable } from "jspdf-autotable";
import { familyName, labNumber, labPercent, type LabResult } from "./lab-contract";

const text = (value: string) => value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^\x20-\x7e\n]/g, "?").slice(0, 2000);
export function labReportModel(result: LabResult) {
  if (result.mode !== "SIMULATION" || result.schema_version !== "lab-result-v1") throw new Error("Only versioned SIMULATION experiments can be exported here.");
  return {
    title: "NetSentinel AI Lab experiment", scope: "SIMULATION - generated metadata; no packets sent", generatedAt: result.generated_at,
    dataset: result.dataset, config: result.config, models: result.models, classification: result.classification, anomaly: result.anomaly,
    performance: result.performance, explanations: result.explanations, limitations: result.limitations,
    // Intentional selection: never serialize arbitrary server metadata, paths or credentials.
    displayedWindows: result.displayed_windows, totalTestWindows: result.total_test_windows,
  };
}
export function createLabPdf(result: LabResult) {
  const model = labReportModel(result);
  const doc = new jsPDF({ unit: "mm", format: "a4", compress: false });
  doc.setProperties({ title: model.title, author: "NetSentinel", subject: model.scope });
  let y = 20;
  const room = (height: number) => { if (y + height > 270) { doc.addPage(); y = 20; } };
  const paragraph = (value: string) => {
    doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.setTextColor(42, 64, 67);
    for (const line of doc.splitTextToSize(text(value), 174) as string[]) { room(5); doc.text(line, 18, y); y += 5; }
    y += 3;
  };
  const heading = (value: string) => {
    doc.setFont("helvetica", "bold"); doc.setFontSize(14); doc.setTextColor(8, 100, 91);
    const lines = doc.splitTextToSize(text(value), 174) as string[];
    room(Math.min(240, lines.length * 7 + 15)); y += 3;
    for (const line of lines) { room(9); doc.text(line, 18, y); y += 7; }
    y += 2;
  };
  const table = (head: string[], rows: string[][]) => {
    autoTable(doc, { startY: y, head: [head], body: rows.map(row => row.map(text)), margin: { top: 20, bottom: 24, left: 18, right: 18 }, styles: { fontSize: 8, cellPadding: 2.5, overflow: "linebreak" }, headStyles: { fillColor: [15, 91, 84] }, pageBreak: "avoid", rowPageBreak: "avoid", theme: "striped" });
    y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
  };
  doc.setFont("helvetica", "bold"); doc.setFontSize(24); doc.setTextColor(8, 100, 91); doc.text("NetSentinel AI Lab", 18, y); y += 11;
  paragraph(model.scope);
  paragraph(`Experiment completed (UTC): ${model.generatedAt}\nReport generated (UTC): ${new Date().toISOString()}\nPeriod: the selected complete generated experiment. Virtual observations are ten-second windows; elapsed processing uses wall-clock seconds.`);
  paragraph("Research question: how well can statistical deviation and behaviour classification distinguish generated workloads on unseen runs? Results describe this simulator, not real-world intrusion accuracy. An anomaly is not an attack. No security control actions are performed.");
  heading("Reproducibility and observation coverage");
  table(["Setting", "Value"], Object.entries(model.config).map(([key, value]) => [key, String(value)]));
  paragraph(`Dataset SHA-256: ${model.dataset.sha256}`);
  table(["Total windows", "Valid", "Unscored", "Metadata events"], [[String(model.dataset.total_windows), String(model.dataset.valid_windows), String(model.dataset.unscored_windows), String(model.dataset.event_count)]]);
  table(["Partition", "Independent runs", "Windows"], Object.entries(model.dataset.splits).map(([name, split]) => [name, String(split.run_ids.length), String(split.windows)]));
  paragraph("Whole runs are assigned to train, validation and test. Missing observations are unscored, never filled with zeros. Isolation Forest fits benign training windows and calibrates on benign validation. The classifier sees numeric features, not scenario labels or seeds.");
  heading("Computed model comparison");
  table(["Model", "Accuracy", "Balanced accuracy", "Macro F1"], model.classification.map(row => [row.model, labPercent(row.accuracy), labPercent(row.balanced_accuracy), labNumber(row.macro_f1)]));
  paragraph("Classification predicts a generated behaviour family, not malicious intent. The dummy and heuristic rules are baselines. Metrics use the same scored test partition; null denotes an unavailable denominator.");
  room(model.classification.length * 10 + 22); heading("Macro F1 comparison (0 to 1)");
  for (const row of model.classification) {
    doc.setFontSize(8); doc.setTextColor(42, 64, 67); doc.text(text(row.model).slice(0, 26), 18, y + 3);
    if (row.macro_f1 !== null) { doc.setFillColor(16, 133, 120); doc.rect(75, y, Math.max(0, Math.min(1, row.macro_f1)) * 90, 4, "F"); }
    doc.text(labNumber(row.macro_f1), 172, y + 3); y += 10;
  }
  for (const classifier of model.classification) {
    heading(`${classifier.model}: test confusion matrix`);
    paragraph("Rows are injected truth; columns are predicted family. Values count scored windows. Ground truth is used only for evaluation.");
    table(["Truth / prediction", ...classifier.labels.map(familyName)], classifier.confusion_matrix.map((row, index) => [familyName(classifier.labels[index]), ...row.map(String)]));
    table(["Family", "Precision", "Recall", "F1", "Support"], classifier.per_class.map(row => [familyName(row.label), labNumber(row.precision), labNumber(row.recall), labNumber(row.f1), String(row.support)]));
  }
  heading("Isolation Forest deviation");
  table(["Metric", "Value"], Object.entries(model.anomaly).map(([key, value]) => [key.replaceAll("_", " "), labNumber(value)]));
  paragraph("False alerts per hour uses benign virtual observation time. Average precision ranks injected challenge labels by deviation. Deviation scores and classifier output are not attack probabilities; legitimate bulk transfers can also look unusual.");
  heading("Selected explanation evidence");
  if (!model.explanations.length) paragraph("No explanation evidence was available for the selected experiment.");
  for (const explanation of model.explanations.slice(0, 8)) {
    // Keep each bounded seven-feature case with its heading and evidence table.
    room(120);
    heading(`Window ${explanation.window_id}`);
    paragraph(`Method: ${explanation.method}\nPredicted family: ${familyName(explanation.predicted_family)}\nBase: ${labNumber(explanation.base_value)}; output: ${labNumber(explanation.output_value)}; additivity error: ${labNumber(explanation.additivity_error, 8)}.`);
    table(["Feature", "Observed", "Training p95", "Contribution"], explanation.features.map(feature => [feature.feature, labNumber(feature.value), labNumber(feature.reference_p95), labNumber(feature.contribution, 5)]));
  }
  paragraph(`Explanation cases shown: ${Math.min(8, model.explanations.length)} of ${model.explanations.length}. The JSON export retains all recorded explanation cases. Contributions explain model output, not causation or proof of an attack.`);
  heading("Measured runtime");
  table(["Measure", "Value"], Object.entries(model.performance).map(([key, value]) => [key.replaceAll("_", " "), labNumber(value)]));
  heading("Limits and privacy");
  paragraph(`Timeline available: ${model.displayedWindows} of ${model.totalTestWindows} test windows. Evaluation uses its recorded scored set, not only chart points. This report has no real IP addresses, executable paths or location inventory. No third-party request is made during export. PDF core fonts transliterate accents; unsupported glyphs appear as ?.`);
  model.limitations.forEach(paragraph);
  const pages = doc.getNumberOfPages();
  for (let page = 1; page <= pages; page++) { doc.setPage(page); doc.setDrawColor(185, 209, 203); doc.line(18, 278, 192, 278); doc.setFontSize(8); doc.setTextColor(60, 83, 80); doc.text("NetSentinel | SIMULATION research report", 18, 284); doc.text(`${page} / ${pages}`, 192, 284, { align: "right" }); }
  return doc;
}
