# 第2弾：nginx設定ミスによる起動失敗と復旧

## 1. 検証目的

nginxの設定ファイルに意図的な文法ミスを加え、設定エラーがサービスの起動にどのような影響を与えるか確認する。

また、エラーメッセージを使って原因を特定し、設定を修正して復旧する。

## 2. 検証環境

- OS：Ubuntu Server 24.04
- 仮想環境：VirtualBox
- 対象サーバ：tokyo
- Webサーバ：nginx

※ 自宅の検証環境でのみ実施。

## 3. 正常状態の確認

```bash
systemctl is-active nginx
sudo nginx -t
curl -I http://localhost
```

正常時には `active`、設定検査の成功、`HTTP/1.1 200 OK` を確認する。

## 4. 設定ファイルのバックアップ

```bash
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
```

バックアップ先は既存ファイルと重複しない名前を使用する。

## 5. 障害の再現

nanoで設定ファイルを開く。

```bash
sudo nano /etc/nginx/nginx.conf
```

次の設定を探す。

```nginx
worker_processes auto;
```

末尾のセミコロンを削除する。

```nginx
worker_processes auto
```

保存後、設定を検査する。

```bash
sudo nginx -t
```

実際の検証では、`worker_processes` の引数に関するエラーが発生した。

## 6. 障害の切り分け

設定ファイルにエラーがあっても、既に動作中のnginxは以前の設定でHTTP 200を返す場合がある。

```bash
curl -I http://localhost
```

実際の検証では、設定ミスがある状態でもHTTP 200を確認した。

その後、検証環境でnginxを停止し、起動を試みたところ失敗した。

```bash
sudo systemctl stop nginx
sudo systemctl start nginx
```

起動失敗後は、サービス状態とログを確認する。

```bash
systemctl status nginx --no-pager
sudo journalctl -u nginx -n 30 --no-pager
```

設定検査の失敗と起動失敗を照らし合わせ、設定ファイルの文法ミスが原因であることを確認する。

## 7. 修正と復旧

nanoで設定を修正し、削除したセミコロンを戻す。

```nginx
worker_processes auto;
```

設定検査を行う。

```bash
sudo nginx -t
```

正常であることを確認してから、nginxを起動する。

```bash
sudo systemctl start nginx
```

最後に、サービス状態とHTTP通信を確認する。

```bash
systemctl is-active nginx
curl -I http://localhost
```

実際の検証では、設定修正後にnginxが起動し、HTTP 200を確認できた。

## 8. 今回の検証で学んだこと

- nginxの設定では、命令の区切りとなるセミコロンが重要
- `nginx -t` で設定ファイルを検査できる
- 設定ファイルの異常と、稼働中のサービスの状態は別
- 起動失敗時には `systemctl` と `journalctl` を組み合わせる
- 設定を修正した後は、起動状態とHTTP通信まで確認する

## 9. 注意事項

本手順は自宅の検証環境で行った障害再現である。

本番環境では、設定ミスを再現するために稼働中のサービスを停止してはいけない。変更前のバックアップ、設定検査、影響確認、承認などの手順を優先する。
