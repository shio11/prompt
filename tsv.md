##対象のExcelファイルで、Excel上の「自動化」タブ → 新しいスクリプトを作成し、TSVテキストを引数として受け取り、行/列に分解してテーブルへ一括追加するスクリ
function main(workbook: ExcelScript.Workbook, tsvText: string) {
  const table = workbook.getWorksheet("Sheet1").getTable("仕様表");
  const rows = tsvText.trim().split("\n").slice(1); // ヘッダー除く
  const data = rows.map(r => r.split("\t"));
  table.addRows(-1, data);
}
