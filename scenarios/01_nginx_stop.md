# 第1弾：nginx停止障害の調査と復旧

## 1. 検証目的

Ubuntu Server上で稼働するnginxを意図的に停止し、障害発生時にどのような症状が現れるのかを確認する。

また、サービスの状態・ポート・ログを調査し、復旧後にHTTP通信が正常に戻ることを確認する。

## 2. 検証環境

- OS：Ubuntu Server 24.04
- 仮想環境：VirtualBox
- 対象サーバ：tokyo
- Webサーバ：nginx

※ 自宅の検証環境でのみ実施する。

## 3. 正常状態の確認

nginxのサービス状態を確認する。

```bash
systemctl status nginx --no-pager
```

HTTP通信を確認する。

```bash
curl -I http://localhost
```

正常な場合、以下のような結果になる。

```text
Active: active (running)
HTTP/1.1 200 OK
```

## 4. 障害の再現

nginxを意図的に停止する。

```bash
sudo systemctl stop nginx
```

サービス状態を確認する。

```bash
systemctl is-active nginx
```

停止していれば、以下のように表示される。

```text
inactive
```

## 5. 障害発生時の切り分け

HTTP通信を確認する。

```bash
curl -I http://localhost
```

nginxが停止し、ほかに80番ポートで待ち受けるサービスがなければ、接続拒否が発生する。

続いて、80番ポートの待ち受け状態を確認する。

```bash
sudo ss -lntp | grep ':80'
```

サービスのログを確認する。

```bash
sudo journalctl -u nginx -n 30 --no-pager
```

これらの情報を組み合わせ、サービス停止がHTTP接続失敗の原因であるかを判断する。

## 6. 復旧

nginxを起動する。

```bash
sudo systemctl start nginx
```

サービス状態を確認する。

```bash
systemctl is-active nginx
```

HTTP通信を再確認する。

```bash
curl -I http://localhost
```

正常に復旧した場合、以下の結果が期待される。

```text
active
HTTP/1.1 200 OK
```

## 7. 今回の検証で学んだこと

- HTTP通信の失敗だけで原因を断定しない
- `systemctl` でサービス状態を確認する
- `ss` でポートの待ち受け状態を確認する
- `journalctl` でサービスの動作履歴を確認する
- 復旧後はHTTP通信まで確認する

## 8. 注意事項

本手順は、自宅の仮想マシンで実施した学習用の検証記録である。

実際の本番環境では、サービス停止の影響範囲や作業権限を確認し、所定の変更管理手順に従う必要がある。
