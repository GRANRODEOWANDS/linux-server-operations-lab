# 第7弾：Linuxのバックアップと復元（cp・tar・rsync）

## 1. 検証目的

Linuxサーバの設定ファイルを想定した練習用ファイルを使い、バックアップの作成から復元、復元結果の確認までを実施する。

今回検証したのは、次の4つ。

- `cp` によるファイルのコピー
- `tar` による複数ファイルのアーカイブ化
- `tar.gz` による圧縮バックアップと復元
- `rsync` によるファイルの同期

単にバックアップを作成するだけでなく、**元のファイルと復元したファイルの内容が一致するか**を確認する。

## 2. 検証環境

- OS：Ubuntu Server 24.04
- 仮想環境：VirtualBox
- 対象サーバ：tokyo
- 作業ディレクトリ：`/home/tokyo/backup-restore-practice/`
- 検証用ファイル：`server.conf`、`network.conf`、`service.conf`

本検証では、本物のシステム設定ファイルではなく、練習用ファイルを使用した。

## 3. バックアップの基本：cp

`cp` はファイルをコピーするコマンド。

例えば、設定ファイルを別名で保存する場合は次のように使用する。

```bash
cp server.conf server.conf.bak
```

コピー後は、元のファイルとバックアップを比較できる。

```bash
diff server.conf server.conf.bak
```

`diff` で何も表示されなければ、ファイルの内容に差分がないことを意味する。

今回の検証では、`cp` によるバックアップと復元の基本操作を実施した。

## 4. tarによる複数ファイルのバックアップ

`tar` は複数のファイルを1つのアーカイブにまとめるために使用できる。

今回の3ファイルをまとめる場合は、次のコマンドを使用する。

```bash
tar -cvf config_backup.tar server.conf network.conf service.conf
```

主なオプションの意味は次のとおり。

| オプション | 意味 |
|---|---|
| `-c` | アーカイブを作成する |
| `-v` | 処理したファイル名を表示する |
| `-f` | アーカイブファイル名を指定する |

作成したアーカイブの内容は、次のコマンドで確認できる。

```bash
tar -tvf config_backup.tar
```

通常のtarアーカイブは、ファイルをまとめるものであり、必ずしも圧縮されているわけではない。

## 5. tarからの復元

復元先ディレクトリを用意する。

```bash
mkdir restore-test
```

アーカイブからファイルを取り出す。

```bash
tar -xvf config_backup.tar -C restore-test
```

ここで使用した主なオプションは以下のとおり。

- `-x`：アーカイブからファイルを取り出す
- `-C restore-test`：取り出し先のディレクトリを指定する

`-c` と `-C` は異なるオプションであり、大文字と小文字を区別する。

復元後は、元のファイルと比較して内容が一致しているか確認する。

```bash
diff server.conf restore-test/server.conf
```

## 6. tar.gzによる圧縮バックアップ

gzip圧縮したアーカイブを作成する。

```bash
tar -czvf config_backup.tar.gz server.conf network.conf service.conf
```

`-z` はgzip圧縮を使用する指定である。

復元先を作成する。

```bash
mkdir restore-gzip-test
```

圧縮アーカイブからファイルを取り出す。

```bash
tar -xzvf config_backup.tar.gz -C restore-gzip-test
```

実際の検証では、次の3ファイルが取り出された。

```text
server.conf
network.conf
service.conf
```

## 7. 通常のtarと圧縮tarの復元結果を比較

2つの復元先をまとめて比較する。

```bash
diff -r restore-test restore-gzip-test
```

実際の検証では差分が表示されなかった。

これにより、**通常のtarと圧縮tarから復元したファイルの内容が一致している**ことを確認できた。

なお、`diff` は主に内容の比較であり、所有者・権限・更新日時などの属性がすべて一致することまで保証するものではない。

## 8. rsyncによるファイル同期

まず、rsyncが利用できるか確認する。

```bash
rsync --version
```

今回の環境では、rsync 3.2.7がインストールされていた。

同期先ディレクトリを作成する。

```bash
mkdir rsync-test
```

実際にコピーする前に、dry-runで対象を確認する。

```bash
rsync -avn server.conf network.conf service.conf rsync-test/
```

主なオプションの意味は次のとおり。

- `-a`：ファイル属性などを保持するアーカイブモード
- `-v`：処理内容を表示する
- `-n`：実際にはコピーしない（dry-run）

今回のdry-runでは、3つのファイルが同期対象として表示された。

続いて、実際に同期する。

```bash
rsync -av server.conf network.conf service.conf rsync-test/
```

初回は3つのファイルが転送対象として表示された。

同じコマンドを再実行すると、ファイル名は表示されなかった。

これは、rsyncが転送を必要とするファイルを見つけなかったことを示している。

## 9. 1ファイルだけ変更して再同期

`network.conf` をnanoで編集する。

```bash
nano network.conf
```

次の値を変更する。

変更前：

```ini
status=normal
```

変更後：

```ini
status=updated
```

保存後、再度rsyncを実行する。

```bash
rsync -av server.conf network.conf service.conf rsync-test/
```

実際の検証では、次のファイルだけが表示された。

```text
network.conf
```

コピー先の内容を確認する。

```bash
cat rsync-test/network.conf
```

実際の結果は次のとおり。

```ini
hostname=tokyo
network=192.168.56.0/24
status=updated
```

これにより、変更したファイルの内容が同期先へ反映されたことを確認した。

## 10. バックアップと同期の違い

`rsync` はファイルの同期に便利だが、同期先に過去の正常な状態が残るとは限らない。

例えば、誤って変更した設定ファイルを同期すると、その誤った内容も同期先へ反映される可能性がある。

そのため、実際のバックアップ運用では、次の点も検討する必要がある。

- 過去の状態を残す世代管理
- バックアップの保存先とアクセス権限
- 定期的な復元テスト
- バックアップ失敗時の検知
- 誤操作による削除・上書きへの対策

今回の検証は、これらの運用設計を完成させたものではなく、基本操作と復元確認を学ぶための実験である。

## 11. 今回の検証で学んだこと

- `cp` はファイル単位のコピーに使用できる
- `tar` は複数ファイルを1つにまとめられる
- `tar.gz` はgzip圧縮したアーカイブである
- `tar -xvf` と `tar -xzvf` でファイルを復元できる
- `diff` で復元前後の内容を比較できる
- `rsync --dry-run` で同期予定のファイルを確認できる
- `rsync` は変更が必要なファイルを効率的に同期できる
- バックアップは作成だけでなく、復元確認が重要である

## 12. 注意事項

本検証は、自宅の仮想マシン上で実施した学習用の記録である。

実際の運用では、バックアップ先の容量、ファイルの権限、復元手順、世代管理、情報保護なども考慮する必要がある。

また、`rsync` のオプションによっては同期先のファイルを削除・上書きするため、実行前の確認が重要である。
