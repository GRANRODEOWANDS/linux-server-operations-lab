# 第6弾：SSH接続障害の切り分け

## 1. 検証目的

LinuxサーバへSSH接続できない場合を想定し、サービス状態、ポート番号、認証方式、ログを確認する方法を学ぶ。

今回は、正常なSSHサービスを使用しながら、次の2つの異常を意図的に再現した。

- 待ち受けていない2222番ポートへ接続する
- クライアント側で認証方式を無効にして認証を失敗させる

接続段階と認証段階の違いを理解することを目的とする。

## 2. 検証環境

- OS：Ubuntu Server 24.04
- 仮想環境：VirtualBox
- 対象サーバ：tokyo
- SSHサービス：OpenSSH Server
- SSH待ち受けポート：22
- 接続先：localhost（127.0.0.1）

※ 自宅の仮想マシン上で実施した検証。

## 3. 正常状態の確認

SSHサービスの状態を確認する。

```bash
systemctl status ssh --no-pager
```

実際の検証では、以下の状態を確認した。

```text
Active: active (running)
```

次に、SSHの待ち受けポートを確認する。

```bash
sudo ss -lntp | grep ':22'
```

実際の検証では、次のアドレスで22番ポートが待ち受けていた。

```text
0.0.0.0:22
[::]:22
```

`0.0.0.0:22` はIPv4の全インターフェース、`[::]:22` はIPv6の全インターフェースで22番ポートを待ち受ける設定を示す。

## 4. 接続拒否の再現

SSHが待ち受けていない2222番ポートへ接続する。

```bash
ssh -p 2222 -o ConnectTimeout=5 localhost
```

実際の検証では、次のエラーが表示された。

```text
ssh: connect to host localhost port 2222: Connection refused
```

次に、2222番ポートの待ち受け状態を確認する。

```bash
sudo ss -lntp '( sport = :2222 )'
```

結果は見出しのみで、2222番ポートを待ち受けるプロセスは表示されなかった。

この検証では、指定したポートにSSHサービスが待ち受けていないことを確認できた。

なお、一般的にはファイアウォールなどが接続を拒否する場合もあるため、`Connection refused` だけで原因を断定しない。

## 5. 正常な22番ポートへの接続

次に、SSHが待ち受けている22番ポートへ接続する。

```bash
ssh -p 22 -o ConnectTimeout=5 localhost hostname
```

初回接続時にはホスト鍵の確認が表示された。

検証環境で接続先を確認したうえで接続を続行し、パスワード認証を行った。

実際の検証では、次の結果が返ってきた。

```text
tokyo
```

これは、SSH接続と認証が成功し、接続先で `hostname` コマンドが実行されたことを示す。

※ 実際の運用では、初回接続時のホスト鍵の指紋を信頼できる情報と照合することが重要である。

## 6. 認証失敗の再現

今回は、SSHサーバの設定を変更せず、クライアント側で利用する認証方式を制限した。

```bash
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=none -o NumberOfPasswordPrompts=0 -o ConnectTimeout=5 localhost hostname
```

実際の検証では、次のエラーが表示された。

```text
tokyo@localhost: Permission denied (publickey,password).
```

これは、SSHサーバへの接続処理は進んだものの、認証が完了しなかったことを示す。

今回の失敗は、クライアント側で意図的に認証方式を制限した結果であり、SSHサーバが故障したわけではない。

## 7. SSHログの調査

SSHサービスのログを確認する。

```bash
sudo journalctl -u ssh -n 30 --no-pager
```

さらに、直近の `sshd` のログを確認する。

```bash
sudo journalctl -t sshd --since "10 minutes ago" --no-pager
```

実際の検証では、正常なパスワード認証に対して次のログを確認した。

```text
Accepted password for tokyo from 127.0.0.1
```

一方、認証を完了させなかった接続では、次のようなログを確認した。

```text
Connection closed by authenticating user tokyo 127.0.0.1 ... [preauth]
```

`preauth` は認証完了前の段階を示す。

このログだけで、パスワードの入力ミスがあったと断定することはできない。

## 8. SSHの有効な設定を確認

最後に、SSHサーバの設定を確認した。

```bash
sudo sshd -T | grep -E '^(port|pubkeyauthentication|passwordauthentication|permitrootlogin) '
```

実際の検証結果は以下のとおり。

```text
port 22
permitrootlogin without-password
pubkeyauthentication yes
passwordauthentication yes
```

この結果から、基本設定として22番ポートを使用し、公開鍵認証とパスワード認証が有効になっていることを確認した。

`permitrootlogin without-password` は、rootユーザーのパスワードによるSSHログインを許可しない設定を示す。

なお、接続元やユーザーに応じた `Match` 設定などがある場合は、実際の接続条件によって有効な設定が異なる可能性がある。

## 9. 今回の検証で学んだこと

- SSHの標準ポートは22番だが、設定によって変更できる
- `systemctl` でSSHサービスの稼働状態を確認できる
- `ss` でポートの待ち受け状態を確認できる
- `Connection refused` と `Permission denied` は異なる段階のエラー
- `journalctl` でSSHの認証履歴を調査できる
- `sshd -T` でSSHサーバの設定を確認できる
- エラーメッセージだけで原因を断定せず、サービス・ポート・ログを組み合わせて調査する

## 10. 注意事項

本検証では、SSHサービスを停止したり、SSHサーバの設定を変更したりしていない。

本番環境でSSH設定を変更する場合は、接続不能になるリスクがあるため、既存セッションの保持、代替接続手段、設定の事前検査などを考慮する必要がある。

また、秘密鍵やパスワードをGitHubに公開してはいけない。
