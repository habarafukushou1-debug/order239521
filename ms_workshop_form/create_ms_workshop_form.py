"""広島県倫理法人会 MS研修会 申し込みフォームを Python で作成するスクリプト。

Google Forms API / Google Sheets API を使い、Apps Script 版
(createMSWorkshopForm) と同じ内容のフォームと回答保存用スプレッドシートを作成します。

事前準備は README.md を参照してください。
"""

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

FORM_TITLE = "広島県倫理法人会 MS研修会 申し込みフォーム"
SPREADSHEET_TITLE = "広島県倫理法人会 MS研修会 申し込み回答"

DESCRIPTION = (
    "日時：2026年12月2日（水）13:00〜15:00\n"
    "受付：12:45〜\n"
    "会場：RCCエリエールA館6階 会議室2（Room2）／広島駅前\n\n"
    "【研修会の目的】\n"
    "全国統一MSマニュアルに沿った運営を役職者が習得し、"
    "どの単会でも質の高いモーニングセミナーを維持すること。\n"
    "出席率向上と入会につながる魅力ある場をつくることを目指します。"
)

# 所属単会の選択肢（実行前に県内の単会名を確認してください）
UNITS = [
    "広島市倫理法人会",
    "広島市中区倫理法人会",
    "広島中央倫理法人会",
    "広島西倫理法人会",
    "廿日市市倫理法人会",
    "東広島市倫理法人会",
    "尾道市倫理法人会",
    "三原市準倫理法人会",
    "福山市倫理法人会",
    "福山北倫理法人会",
    "呉市倫理法人会",
    "呉あきなだ倫理法人会",
    "三次・庄原倫理法人会",
]


def get_credentials():
    """OAuth 認証を行い、認証情報を返す（2回目以降は token.json を再利用）。"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def text_item(title, required, paragraph=False):
    return {
        "title": title,
        "questionItem": {
            "question": {
                "required": required,
                "textQuestion": {"paragraph": paragraph},
            }
        },
    }


def choice_item(title, options, choice_type, required):
    return {
        "title": title,
        "questionItem": {
            "question": {
                "required": required,
                "choiceQuestion": {
                    "type": choice_type,  # "DROP_DOWN" / "RADIO" / "CHECKBOX"
                    "options": [{"value": v} for v in options],
                },
            }
        },
    }


def create_form(forms_service):
    # 1. フォームの基本設定（create ではタイトルしか指定できない）
    form = forms_service.forms().create(
        body={"info": {"title": FORM_TITLE, "documentTitle": FORM_TITLE}}
    ).execute()
    form_id = form["formId"]

    items = [
        # 2. 所属単会（プルダウン）
        choice_item("所属単会", UNITS, "DROP_DOWN", True),
        # 3. お名前
        text_item("お名前", True),
        # 4. 会社名
        text_item("会社名", False),
        # 5. 出欠（ラジオボタン）
        choice_item("出欠", ["出席", "欠席"], "RADIO", True),
        # 6. 質問・メッセージ（段落）
        text_item("質問やメッセージがあれば", False, paragraph=True),
    ]

    requests = [
        {
            "updateFormInfo": {
                "info": {"description": DESCRIPTION},
                "updateMask": "description",
            }
        }
    ]
    for index, item in enumerate(items):
        requests.append(
            {"createItem": {"item": item, "location": {"index": index}}}
        )

    forms_service.forms().batchUpdate(
        formId=form_id, body={"requests": requests}
    ).execute()

    # API で作成したフォームは未公開の場合があるため、公開して回答受付を開始する
    forms_service.forms().setPublishSettings(
        formId=form_id,
        body={
            "publishSettings": {
                "publishState": {"isPublished": True, "isAcceptingResponses": True}
            },
            "updateMask": "publishState",
        },
    ).execute()

    return forms_service.forms().get(formId=form_id).execute()


def create_spreadsheet(sheets_service):
    # 7. 回答保存用のスプレッドシートを作成し、見出し行を書き込む
    spreadsheet = sheets_service.spreadsheets().create(
        body={"properties": {"title": SPREADSHEET_TITLE}},
        fields="spreadsheetId,spreadsheetUrl",
    ).execute()
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet["spreadsheetId"],
        range="A1",
        valueInputOption="RAW",
        body={
            "values": [
                ["タイムスタンプ", "所属単会", "お名前", "会社名", "出欠", "質問やメッセージ"]
            ]
        },
    ).execute()
    return spreadsheet


def main():
    creds = get_credentials()
    forms_service = build("forms", "v1", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    form = create_form(forms_service)
    spreadsheet = create_spreadsheet(sheets_service)

    # 8. 作成結果を表示
    form_id = form["formId"]
    print("フォームID：" + form_id)
    print("フォーム編集URL：https://docs.google.com/forms/d/" + form_id + "/edit")
    print("回答用URL：" + form["responderUri"])
    print("回答保存先：" + spreadsheet["spreadsheetUrl"])
    print()
    print("※ 回答をスプレッドシートへ転記するには次を実行してください：")
    print(
        f"   python sync_responses.py {form_id} {spreadsheet['spreadsheetId']}"
    )


if __name__ == "__main__":
    main()
