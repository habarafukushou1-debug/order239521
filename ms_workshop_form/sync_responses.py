"""フォームの回答をスプレッドシートへ転記するスクリプト。

Forms API では「回答の保存先スプレッドシート」を設定できないため、
このスクリプトで回答を取得して書き込みます（実行するたびに全件を書き直します）。

使い方: python sync_responses.py <フォームID> <スプレッドシートID>
"""

import sys

from googleapiclient.discovery import build

from create_ms_workshop_form import get_credentials

HEADER = ["タイムスタンプ", "所属単会", "お名前", "会社名", "出欠", "質問やメッセージ"]


def main(form_id, spreadsheet_id):
    creds = get_credentials()
    forms_service = build("forms", "v1", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    # 質問タイトル → questionId の対応を作る
    form = forms_service.forms().get(formId=form_id).execute()
    question_ids = {
        item["title"]: item["questionItem"]["question"]["questionId"]
        for item in form.get("items", [])
        if "questionItem" in item
    }

    responses = []
    page_token = None
    while True:
        result = forms_service.forms().responses().list(
            formId=form_id, pageToken=page_token
        ).execute()
        responses.extend(result.get("responses", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    responses.sort(key=lambda r: r["lastSubmittedTime"])

    rows = [HEADER]
    for r in responses:
        answers = r.get("answers", {})
        row = [r["lastSubmittedTime"]]
        for title in HEADER[1:]:
            answer = answers.get(question_ids.get(title), {})
            values = answer.get("textAnswers", {}).get("answers", [])
            row.append(", ".join(v.get("value", "") for v in values))
        rows.append(row)

    sheets_service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id, range="A:Z"
    ).execute()
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()
    print(f"{len(responses)} 件の回答を書き込みました。")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("使い方: python sync_responses.py <フォームID> <スプレッドシートID>")
    main(sys.argv[1], sys.argv[2])
