# 第3弾：403 Forbiddenとファイル権限の調査・復旧

## 1. 検証目的

nginxが正常に起動していても、Webページへのアクセスが失敗するケースを検証する。

今回は、Web公開ディレクトリ内のファイル権限を意図的に変更し、HTTP 403 Forbiddenを発生させる。

サービス状態、HTTPレスポンス、エラーログを確認し、原因を特定して復旧する。

## 2. 検証環境

- OS：Ubuntu Server 24.04
- 仮想環境：VirtualBox
- 対象サーバ：tokyo
- Webサーバ：nginx
- 検証用ファイル：`/var/www/html/permission-test.html`

※ 自宅の仮想環境で実施した検証。

## 3. 正常状態の確認

nginxが起動しているか確認する。

```bash
systemctl is-active nginx
```

検証用ファイルを用意し、HTTP通信を確認する。

```bash
curl -I http://localhost/permission-test.html
```

正常時には以下の結果を確認した。

```text
HTTP/1.1 200 OK
```

## 4. 障害の再現

検証用ファイルの権限を変更する。

```bash
sudo chmod 000 /var/www/html/permission-test.html
```

`000` は、所有者・グループ・その他のユーザーすべてに対して、読み取り・書き込み・実行権限を与えない設定である。

HTTP通信を再確認する。

```bash
curl -I http://localhost/permission-test.html
```

実際の検証では、以下の結果を確認した。

```text
HTTP/1.1 403 Forbidden
```

## 5. 原因の切り分け

nginxのサービス状態を確認する。

```bash
systemctl is-active nginx
```

サービスが起動していても、対象ファイルへのアクセスが失敗する場合がある。

続いて、nginxのエラーログを確認する。

```bash
sudo tail -n 30 /var/log/nginx/error.log
```

実際の検証では、以下の内容を確認した。

```text
open() ... failed (13: Permission denied)
```

これは、nginxが対象ファイルを開こうとした際、権限不足によって拒否されたことを示す。

## 6. 修正と復旧

検証用ファイルの権限を戻す。

```bash
sudo chmod 644 /var/www/html/permission-test.html
```

`644` は、所有者に読み取り・書き込み権限、グループとその他のユーザーに読み取り権限を与える設定である。

再度HTTP通信を確認する。

```bash
curl -I http://localhost/permission-test.html
```

実際の検証では、HTTP 200に戻ったことを確認した。

また、nginxの標準ページについてもHTTP 200を確認した。

## 7. 今回の検証で学んだこと

- nginxが起動していても、Webページが正常に表示されるとは限らない
- HTTP 403はアクセスが拒否されたことを示す
- `chmod` でファイル権限を変更できる
- `error.log` を確認すると、アクセス失敗の原因を調べられる
- 修正後は対象ページに再アクセスして復旧を確認する

## 8. 注意事項

本検証では、専用のテストファイルに対してのみ権限を変更した。

本番環境で無闇に `chmod 000` や `chmod 777` を実行すると、サービス障害やセキュリティ上の問題につながる可能性がある。

権限を変更する前には、対象ファイル、所有者、実行ユーザー、必要な権限を確認する。
