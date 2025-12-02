# コントリビューションガイド

このドキュメントでは、プロジェクトへの貢献方法と、コードを追加する際のドキュメント作成ガイドラインを説明します。

---

## 目次

1. [コードスタイル](#コードスタイル)
2. [ドキュメント作成ガイドライン](#ドキュメント作成ガイドライン)
3. [コミットメッセージ](#コミットメッセージ)
4. [プルリクエスト](#プルリクエスト)

---

## コードスタイル

### 一般的なガイドライン

- 明確で説明的な変数名・関数名を使用する
- 単一責任の原則に従う
- DRY（Don't Repeat Yourself）を心がける
- テストを書く

---

## ドキュメント作成ガイドライン

### JavaScript/TypeScript

JSDoc形式でドキュメントを記載してください：

```javascript
/**
 * 2つの数値を加算します。
 *
 * @param {number} a - 最初の数値
 * @param {number} b - 2番目の数値
 * @returns {number} 2つの数値の合計
 * @throws {TypeError} 引数が数値でない場合
 *
 * @example
 * const result = add(2, 3);
 * console.log(result); // 5
 */
function add(a, b) {
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new TypeError('引数は数値である必要があります');
  }
  return a + b;
}
```

### TypeScript (型定義付き)

```typescript
/**
 * ユーザー情報を表すインターフェース
 */
interface User {
  /** ユーザーの一意識別子 */
  id: string;
  /** ユーザー名 */
  name: string;
  /** メールアドレス（オプション） */
  email?: string;
}

/**
 * ユーザー情報を取得します。
 *
 * @param userId - 取得するユーザーのID
 * @returns ユーザー情報を含むPromise
 * @throws {NotFoundError} ユーザーが見つからない場合
 *
 * @example
 * const user = await getUser('user-123');
 * console.log(user.name);
 */
async function getUser(userId: string): Promise<User> {
  // 実装
}
```

### Python

Docstring形式（Google スタイル）でドキュメントを記載してください：

```python
def calculate_average(numbers: list[float]) -> float:
    """数値リストの平均を計算します。

    与えられた数値のリストから算術平均を計算して返します。
    空のリストが渡された場合は0.0を返します。

    Args:
        numbers: 平均を計算する数値のリスト

    Returns:
        数値リストの算術平均

    Raises:
        TypeError: リストに数値以外の要素が含まれている場合

    Example:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
        >>> calculate_average([])
        0.0
    """
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
```

### Python クラス

```python
class DataProcessor:
    """データ処理を行うクラス。

    大量のデータを効率的に処理するためのユーティリティクラスです。
    バッチ処理とストリーミング処理の両方をサポートしています。

    Attributes:
        batch_size: バッチ処理時の1回あたりの処理件数
        timeout: 処理のタイムアウト時間（秒）

    Example:
        >>> processor = DataProcessor(batch_size=100)
        >>> results = processor.process(data)
    """

    def __init__(self, batch_size: int = 50, timeout: float = 30.0):
        """DataProcessorを初期化します。

        Args:
            batch_size: バッチサイズ（デフォルト: 50）
            timeout: タイムアウト時間（秒）（デフォルト: 30.0）
        """
        self.batch_size = batch_size
        self.timeout = timeout
```

### React コンポーネント

```tsx
import React from 'react';

/**
 * ボタンコンポーネントのプロパティ
 */
interface ButtonProps {
  /** ボタンに表示するテキスト */
  label: string;
  /** ボタンのバリアント */
  variant?: 'primary' | 'secondary' | 'danger';
  /** 無効化状態 */
  disabled?: boolean;
  /** クリック時のコールバック */
  onClick?: () => void;
}

/**
 * 再利用可能なボタンコンポーネント
 *
 * @param props - ボタンのプロパティ
 * @returns ボタン要素
 *
 * @example
 * ```tsx
 * <Button
 *   label="送信"
 *   variant="primary"
 *   onClick={() => handleSubmit()}
 * />
 * ```
 */
export const Button: React.FC<ButtonProps> = ({
  label,
  variant = 'primary',
  disabled = false,
  onClick,
}) => {
  return (
    <button
      className={`btn btn-${variant}`}
      disabled={disabled}
      onClick={onClick}
    >
      {label}
    </button>
  );
};
```

### API エンドポイント

OpenAPI/Swagger形式またはインラインコメントで記載：

```yaml
# OpenAPI 3.0 形式
paths:
  /users/{id}:
    get:
      summary: ユーザー情報の取得
      description: 指定されたIDのユーザー情報を取得します
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
          description: ユーザーID
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: ユーザーが見つかりません
```

---

## コミットメッセージ

以下の形式でコミットメッセージを記載してください：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（空白、フォーマット等）
- `refactor`: バグ修正でも機能追加でもないコード変更
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

### 例

```
feat(auth): ユーザー認証機能を追加

- JWTトークンベースの認証を実装
- ログイン/ログアウトAPIを追加
- リフレッシュトークンをサポート

Closes #123
```

---

## プルリクエスト

### テンプレート

```markdown
## 概要
<!-- 変更内容の概要を記載 -->

## 変更内容
<!-- 具体的な変更点をリスト形式で記載 -->
- 
- 
- 

## テスト方法
<!-- この変更をテストする方法を記載 -->

## チェックリスト
- [ ] テストを追加/更新した
- [ ] ドキュメントを更新した
- [ ] リンターエラーがない
- [ ] セルフレビューを行った
```

---

## 質問・サポート

不明点がある場合は、Issueを作成してください。
