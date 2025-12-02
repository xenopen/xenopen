# コード例集

このドキュメントには、プロジェクトの主要な機能を使用した実践的なコード例が含まれています。

## 目次

1. [基本的な例](#基本的な例)
2. [中級の例](#中級の例)
3. [高度な例](#高度な例)
4. [統合例](#統合例)

---

## 基本的な例

### 例1: 基本的な関数の使用

```javascript
import { basicFunction } from '[パッケージ名]';

// シンプルな関数呼び出し
const result = basicFunction('input');
console.log(result);
// 出力: [期待される出力]
```

---

### 例2: コンポーネントの基本的な使用

```jsx
import React from 'react';
import { Button } from '[パッケージ名]';

function App() {
  return (
    <div>
      <Button onClick={() => console.log('クリックされました')}>
        クリックしてください
      </Button>
    </div>
  );
}
```

---

### 例3: クラスの基本的な使用

```javascript
import { ExampleClass } from '[パッケージ名]';

// インスタンスの作成
const instance = new ExampleClass('param1', 'param2');

// プロパティへのアクセス
console.log(instance.property);

// メソッドの呼び出し
const result = instance.method();
console.log(result);
```

---

## 中級の例

### 例1: 非同期処理

```javascript
import { asyncFunction } from '[パッケージ名]';

async function example() {
  try {
    const result = await asyncFunction({
      param1: 'value1',
      param2: 'value2'
    });
    console.log('成功:', result);
  } catch (error) {
    console.error('エラー:', error);
  }
}

example();
```

---

### 例2: 複数の関数の組み合わせ

```javascript
import { functionA, functionB, functionC } from '[パッケージ名]';

async function combinedExample(input) {
  // ステップ1: 入力の処理
  const step1 = functionA(input);
  
  // ステップ2: 中間処理
  const step2 = functionB(step1);
  
  // ステップ3: 最終処理
  const result = await functionC(step2);
  
  return result;
}

combinedExample('input')
  .then(result => console.log('結果:', result))
  .catch(error => console.error('エラー:', error));
```

---

### 例3: React Hooksの使用

```jsx
import React, { useState, useEffect } from 'react';
import { useCustomHook } from '[パッケージ名]';

function Component() {
  const [data, setData] = useState(null);
  const customData = useCustomHook('param');

  useEffect(() => {
    if (customData) {
      setData(customData);
    }
  }, [customData]);

  return (
    <div>
      {data ? <div>{data}</div> : <div>読み込み中...</div>}
    </div>
  );
}
```

---

## 高度な例

### 例1: エラーハンドリングとリトライ

```javascript
import { unreliableFunction } from '[パッケージ名]';

async function withRetry(input, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await unreliableFunction(input);
      return result;
    } catch (error) {
      if (i === maxRetries - 1) {
        throw error;
      }
      console.log(`リトライ ${i + 1}/${maxRetries}`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}

withRetry('input')
  .then(result => console.log('成功:', result))
  .catch(error => console.error('最終的なエラー:', error));
```

---

### 例2: カスタムフックの作成

```jsx
import { useState, useEffect } from 'react';
import { dataService } from '[パッケージ名]';

function useDataService(endpoint) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const result = await dataService.fetch(endpoint);
        setData(result);
        setError(null);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
}

// 使用例
function Component() {
  const { data, loading, error } = useDataService('/api/data');

  if (loading) return <div>読み込み中...</div>;
  if (error) return <div>エラー: {error.message}</div>;
  return <div>{JSON.stringify(data)}</div>;
}
```

---

### 例3: 型安全な関数の使用（TypeScript）

```typescript
import { TypedFunction } from '[パッケージ名]';

interface InputType {
  name: string;
  age: number;
}

interface OutputType {
  message: string;
  isValid: boolean;
}

async function typedExample(input: InputType): Promise<OutputType> {
  const result = await TypedFunction(input);
  return result;
}

// 使用例
const input: InputType = {
  name: 'John',
  age: 30
};

typedExample(input)
  .then(result => {
    console.log(result.message);
    console.log('有効:', result.isValid);
  });
```

---

## 統合例

### 例1: 完全なアプリケーション例

```jsx
import React, { useState, useEffect } from 'react';
import {
  DataService,
  ValidationService,
  NotificationService
} from '[パッケージ名]';

function CompleteApp() {
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    
    if (!ValidationService.validateEmail(formData.email)) {
      newErrors.email = '無効なメールアドレスです';
    }
    
    if (!ValidationService.validateName(formData.name)) {
      newErrors.name = '名前は必須です';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    
    try {
      const result = await DataService.submit(formData);
      NotificationService.success('送信が完了しました');
      console.log('結果:', result);
    } catch (error) {
      NotificationService.error('送信に失敗しました');
      console.error('エラー:', error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>名前:</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
        {errors.name && <span className="error">{errors.name}</span>}
      </div>
      
      <div>
        <label>メール:</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>
      
      <button type="submit" disabled={submitting}>
        {submitting ? '送信中...' : '送信'}
      </button>
    </form>
  );
}
```

---

### 例2: サーバーサイドの使用例（Node.js）

```javascript
const express = require('express');
const { ApiService } = require('[パッケージ名]');

const app = express();
app.use(express.json());

app.post('/api/process', async (req, res) => {
  try {
    const { input } = req.body;
    
    // 入力の検証
    if (!input) {
      return res.status(400).json({ error: '入力が必要です' });
    }
    
    // 処理の実行
    const result = await ApiService.process(input);
    
    // 結果の返却
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('エラー:', error);
    res.status(500).json({ error: '処理に失敗しました' });
  }
});

app.listen(3000, () => {
  console.log('サーバーが起動しました: http://localhost:3000');
});
```

---

### 例3: テストの例

```javascript
import { describe, it, expect } from '@jest/globals';
import { functionToTest } from '[パッケージ名]';

describe('functionToTest', () => {
  it('正常な入力で正しい結果を返す', () => {
    const result = functionToTest('input');
    expect(result).toBe('expected-output');
  });

  it('無効な入力でエラーを投げる', () => {
    expect(() => {
      functionToTest(null);
    }).toThrow('無効な入力です');
  });

  it('非同期処理が正しく動作する', async () => {
    const result = await functionToTest('input');
    expect(result).toBeDefined();
  });
});
```

---

## パターンとベストプラクティス

### パターン1: オプショナルチェーン

```javascript
import { nestedFunction } from '[パッケージ名]';

// 安全なプロパティアクセス
const result = nestedFunction?.()?.property?.value ?? 'default';
```

---

### パターン2: デストラクチャリング

```javascript
import { functionWithOptions } from '[パッケージ名]';

const options = {
  option1: 'value1',
  option2: 'value2',
  option3: 'value3'
};

const { option1, option2 } = options;
const result = functionWithOptions({ option1, option2 });
```

---

### パターン3: パイプライン処理

```javascript
import { pipe, functionA, functionB, functionC } from '[パッケージ名]';

const process = pipe(
  functionA,
  functionB,
  functionC
);

const result = process('input');
```

---

## トラブルシューティングの例

### 例1: デバッグログの追加

```javascript
import { debugFunction } from '[パッケージ名]';

function debugExample(input) {
  console.log('入力:', input);
  
  try {
    const result = debugFunction(input);
    console.log('結果:', result);
    return result;
  } catch (error) {
    console.error('エラー詳細:', {
      message: error.message,
      stack: error.stack,
      input: input
    });
    throw error;
  }
}
```

---

## 関連ドキュメント

- [API リファレンス](./API_REFERENCE.md) - すべてのAPIの詳細
- [使用ガイド](./USAGE_GUIDE.md) - 詳細な使用方法
- [トラブルシューティング](./TROUBLESHOOTING.md) - 問題解決ガイド
