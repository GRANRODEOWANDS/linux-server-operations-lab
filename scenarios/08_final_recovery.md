# 第8弾：nginx設定ミスの検出とバックアップからの復旧【最終演習】

## 1. 検証目的

これまでのLinux Server Operations Labで学んだ内容を組み合わせ、障害の発見から原因調査、修正、復旧確認までの一連の流れを実践する。

今回の想定シナリオは次のとおり。

**「nginxの設定ファイルを変更したところ、設定検査でエラーが発生した。現在のWebサービスへの影響を確認し、安全に元の状態へ戻す」**

今回は、意図的にnginxの設定ファイルへ文法ミスを加える。

ただし、実際に複数の障害を同時発生させたわけではなく、設定ミスの検出とバックアップからの復元を組み合わせた最終演習である。

## 2. 検証環境

- 仮想環境：VirtualBox
- OS：Ubuntu Server 24.04
- 対象サーバ：tokyo
- Webサーバ：nginx
- 設定ファイル：`/etc/nginx/nginx.conf`
- バックアップ：`/etc/nginx/nginx.conf.phase8.bak`

※ 自宅の検証環境で実施した内容であり、本番環境での作業記録ではない。

## 3. 障害発生前の正常状態を確認

最初にnginxの稼働状態を確認した。

```bash
systemctl status nginx --no-pager
```

実際の検証では、次の状態を確認した。

```text
Active: active (running)
```

続いて、HTTP通信を確認した。

```bash
curl -I http://localhost
```

実際の結果は次のとおり。

```text
HTTP/1.1 200 OK
```

この時点で、nginxが稼働しており、localhostへのHTTP通信が成功していることを確認した。

ただし、HTTP 200が返ってきたことだけで、外部からのアクセスやすべてのWebページが正常であるとは断定できない。

## 4. 正常な設定ファイルをバックアップ

障害を再現する前に、nginxの設定ファイルをバックアップした。

```bash
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.phase8.bak
```

続いて、バックアップ元とバックアップ先の内容を比較した。

```bash
sudo diff /etc/nginx/nginx.conf /etc/nginx/nginx.conf.phase8.bak
```

実際の検証では、差分が表示されなかった。

これにより、バックアップ時点で2つのファイルの内容が一致していることを確認した。

## 5. nginxの設定ミスを意図的に再現

nanoで設定ファイルを開いた。

```bash
sudo nano /etc/nginx/nginx.conf
```

次の設定を探した。

```nginx
worker_processes auto;
```

末尾のセミコロン `;` を削除した。

```nginx
worker_processes auto
```

この変更によって、nginxの設定ファイルに文法上の問題を発生させた。

今回は、設定ファイルを書き換えた段階ではnginxを停止・再起動していない。

## 6. 設定エラーの検出

設定ファイルを検査した。

```bash
sudo nginx -t
```

実際の検証では、次のエラーが発生した。

```text
invalid number of arguments in "worker_processes" directive
in /etc/nginx/nginx.conf:3

nginx: configuration file /etc/nginx/nginx.conf test failed
```

エラーメッセージから、以下の情報を確認した。

| エラーの表示 | 読み取れる内容 |
|---|---|
| `invalid number of arguments` | 設定項目の引数の解釈に問題がある |
| `worker_processes` | 問題が検出された設定項目 |
| `nginx.conf:3` | 問題が検出されたファイルと行番号 |
| `test failed` | 設定検査が失敗した |

今回は、`worker_processes auto;` のセミコロンを削除したことが原因だった。

## 7. 設定エラーがHTTP通信へ影響しているか確認

設定ファイルにエラーがある状態で、HTTP通信を確認した。

```bash
curl -I http://localhost
```

実際の結果は次のとおり。

```text
HTTP/1.1 200 OK
```

設定検査は失敗していたが、HTTP通信は成功した。

これは、nginxが以前に読み込んだ正常な設定で動作を続けていたためと考えられる。

**設定ファイルにエラーがあることと、現在稼働しているサービスが停止していることは別である。**

今回の検証では、設定ミスを発見した段階でサービスを停止させず、復旧を優先した。

## 8. バックアップから設定ファイルを復元

正常時に作成したバックアップを元の設定ファイルへコピーした。

```bash
sudo cp /etc/nginx/nginx.conf.phase8.bak /etc/nginx/nginx.conf
```

これにより、文法ミスを加える前の設定ファイルへ戻した。

この操作では、nginxサービス自体の再起動は行っていない。

## 9. 設定ファイルの復旧確認

復元後に、設定検査を再実行した。

```bash
sudo nginx -t
```

実際の検証では、次の結果を確認した。

```text
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

設定ファイルが正常に戻ったことを確認できた。

## 10. 最終HTTP通信確認

最後に、HTTP通信を再確認した。

```bash
curl -I http://localhost
```

実際の結果は次のとおり。

```text
HTTP/1.1 200 OK
```

設定を復元した後も、Webサーバが正常なHTTPレスポンスを返していることを確認した。

## 11. 今回の障害対応フロー

今回の検証は、次の順番で進めた。

```text
① nginxの稼働状態を確認
          ↓
② HTTP 200を確認
          ↓
③ 正常な設定ファイルをバックアップ
          ↓
④ 設定ファイルに文法ミスを再現
          ↓
⑤ nginx -tでエラーを検出
          ↓
⑥ HTTP通信への影響を確認
          ↓
⑦ バックアップから設定を復元
          ↓
⑧ nginx -tで設定の正常性を確認
          ↓
⑨ HTTP 200を再確認
```

## 12. 今回の検証で学んだこと

- 障害を再現する前に正常状態を確認する
- 設定変更前にバックアップを作成する
- `diff` でバックアップの内容を比較する
- `nginx -t` で設定ファイルのエラーを検出する
- エラーメッセージから問題の設定項目や行番号を調べる
- 設定ファイルの状態と稼働中のサービスの状態を区別する
- 必要のないサービス停止や再起動を避ける
- バックアップから元の設定へ戻す
- 復旧後は設定検査とHTTP通信の両方を確認する

## 13. 今後の改善点

今回は設定ミスを自分で作成し、その原因を知った状態で調査した。

今後は、原因を事前に知らない状態で障害を調査する演習も行いたい。

また、今回実施したのは単一の設定ミスへの対応であり、複数障害が同時に発生した場合の切り分けまでは検証していない。

これらは今後の学習課題とする。

## 14. 注意事項

本手順は、自宅の仮想マシンで実施した学習用の障害再現・復旧記録である。

実際の運用環境では、設定変更前のバックアップ、作業承認、影響範囲の確認、復旧手順の準備などが必要になる。

また、設定ファイルをバックアップから戻す際は、復元によって必要な変更まで失われないか確認する必要がある。

本検証の結果は、実際の本番環境における復旧能力を保証するものではない。
