# API リファレンス

このドキュメントは、プロジェクト内のすべてのパブリックAPI、関数、クラス、コンポーネントの詳細なリファレンスを提供します。

## 目次

- [関数](#関数)
- [クラス](#クラス)
- [インターフェース](#インターフェース)
- [型定義](#型定義)
- [コンポーネント](#コンポーネント)
- [フック](#フック)
- [ユーティリティ](#ユーティリティ)

---

## 関数

### `functionName(param1: Type, param2?: Type): ReturnType`

[関数の詳細な説明]

**パラメータ:**

| パラメータ名 | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `param1` | `Type` | はい | [パラメータ1の説明] |
| `param2` | `Type` | いいえ | [パラメータ2の説明] |

**戻り値:**

`ReturnType`: [戻り値の説明]

**例:**

```typescript
import { functionName } from '[パッケージ名]';

const result = functionName('value1', 'value2');
// result: [期待される結果]
```

**使用例:**

```typescript
// 基本的な使用
const output = functionName('input');

// オプションパラメータ付き
const output2 = functionName('input', { option: true });
```

**エラー:**

- `ErrorType`: [エラーの説明と発生条件]

**関連項目:**

- [関連する関数/クラスへのリンク]

---

## クラス

### `ClassName`

[クラスの説明]

#### コンストラクタ

```typescript
new ClassName(param1: Type, param2: Type)
```

**パラメータ:**

- `param1` (Type): [パラメータ1の説明]
- `param2` (Type): [パラメータ2の説明]

#### プロパティ

##### `property1: Type`

[プロパティ1の説明]

**読み取り専用:** [はい/いいえ]

**例:**

```typescript
const instance = new ClassName('value1', 'value2');
console.log(instance.property1);
```

##### `property2: Type`

[プロパティ2の説明]

#### メソッド

##### `methodName(param: Type): ReturnType`

[メソッドの説明]

**パラメータ:**

- `param` (Type): [パラメータの説明]

**戻り値:**

`ReturnType`: [戻り値の説明]

**例:**

```typescript
const instance = new ClassName('value1', 'value2');
const result = instance.methodName('param');
```

##### `asyncMethod(param: Type): Promise<ReturnType>`

[非同期メソッドの説明]

**パラメータ:**

- `param` (Type): [パラメータの説明]

**戻り値:**

`Promise<ReturnType>`: [戻り値の説明]

**例:**

```typescript
const instance = new ClassName('value1', 'value2');
const result = await instance.asyncMethod('param');
```

---

## インターフェース

### `InterfaceName`

[インターフェースの説明]

```typescript
interface InterfaceName {
  property1: Type;
  property2?: Type;
  method(): ReturnType;
}
```

**プロパティ:**

- `property1` (Type, 必須): [プロパティ1の説明]
- `property2` (Type, オプション): [プロパティ2の説明]

**メソッド:**

- `method()`: [メソッドの説明]

**例:**

```typescript
const obj: InterfaceName = {
  property1: 'value',
  method: () => {
    return 'result';
  }
};
```

---

## 型定義

### `TypeName`

[型の説明]

```typescript
type TypeName = string | number;
```

**使用例:**

```typescript
let value: TypeName = 'string';
value = 123;
```

---

## コンポーネント

### `<ComponentName />`

[コンポーネントの説明]

**インポート:**

```typescript
import { ComponentName } from '[パッケージ名]';
```

**Props:**

```typescript
interface ComponentNameProps {
  prop1: string;
  prop2?: number;
  onClick?: (event: Event) => void;
}
```

| プロパティ名 | 型 | 必須 | デフォルト値 | 説明 |
|------------|-----|------|------------|------|
| `prop1` | `string` | はい | - | [プロパティ1の説明] |
| `prop2` | `number` | いいえ | `0` | [プロパティ2の説明] |
| `onClick` | `(event: Event) => void` | いいえ | - | [イベントハンドラーの説明] |

**例:**

```tsx
import { ComponentName } from '[パッケージ名]';

function App() {
  const handleClick = (event: Event) => {
    console.log('クリックされました', event);
  };

  return (
    <ComponentName
      prop1="value"
      prop2={42}
      onClick={handleClick}
    />
  );
}
```

**スタイリング:**

[スタイリングに関する情報]

**アクセシビリティ:**

[アクセシビリティに関する情報]

---

## フック

### `useHookName(param: Type): ReturnType`

[フックの説明]

**パラメータ:**

- `param` (Type): [パラメータの説明]

**戻り値:**

`ReturnType`: [戻り値の説明]

**例:**

```typescript
import { useHookName } from '[パッケージ名]';

function Component() {
  const result = useHookName('param');
  return <div>{result}</div>;
}
```

**注意事項:**

[使用時の注意事項]

---

## ユーティリティ

### `utilityFunction(input: Type): ReturnType`

[ユーティリティ関数の説明]

**パラメータ:**

- `input` (Type): [入力の説明]

**戻り値:**

`ReturnType`: [戻り値の説明]

**例:**

```typescript
import { utilityFunction } from '[パッケージ名]/utils';

const result = utilityFunction('input');
```

---

## エラー処理

### `CustomError`

[カスタムエラーの説明]

```typescript
class CustomError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'CustomError';
  }
}
```

**使用例:**

```typescript
try {
  // コード
} catch (error) {
  if (error instanceof CustomError) {
    console.error('エラーコード:', error.code);
  }
}
```

---

## イベント

### `EventName`

[イベントの説明]

**イベントタイプ:**

```typescript
type EventName = {
  type: 'event-name';
  payload: {
    // ペイロードの型定義
  };
};
```

**例:**

```typescript
emitter.on('event-name', (event: EventName) => {
  console.log(event.payload);
});
```

---

## 定数

### `CONSTANT_NAME`

[定数の説明]

```typescript
export const CONSTANT_NAME = 'value';
```

**使用例:**

```typescript
import { CONSTANT_NAME } from '[パッケージ名]';

console.log(CONSTANT_NAME);
```

---

## 名前空間

### `NamespaceName`

[名前空間の説明]

```typescript
namespace NamespaceName {
  export function functionName(): void {
    // 実装
  }
}
```

**使用例:**

```typescript
NamespaceName.functionName();
```
