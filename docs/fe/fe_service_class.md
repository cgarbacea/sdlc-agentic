---
tags: [service, HTTP, API client, KyHttpClient, handleLoading, LoadingMode, getRuntimeConfig]
executor: fe
---

# Service Class Pattern

```typescript
// features/<name>/api/<Name>Service.ts
import type { IHttpClient } from "@/lib/api/http-client";
import { KyHttpClient } from "@/lib/api/ky-http-client";
import { getRuntimeConfig } from "@/lib/config";
import { handleLoading, LoadingMode } from "@/lib/decorators/handleLoading";
import type { MyEntity, CreateMyEntityRequest } from "@/types/api";

export class MyFeatureService {
  private _http?: IHttpClient;

  constructor(http?: IHttpClient) {
    this._http = http;
  }

  private get http(): IHttpClient {
    return (this._http ??= new KyHttpClient(`${getRuntimeConfig().apiUrl}/my-domain`));
  }

  @handleLoading({ type: LoadingMode.Background })
  async getEntities(): Promise<MyEntity[]> {
    return this.http.get<MyEntity[]>("entities");
  }

  @handleLoading({ type: LoadingMode.Blocking })
  async createEntity(req: CreateMyEntityRequest): Promise<MyEntity> {
    return this.http.post<MyEntity>("entities", { json: req });
  }
}

export const myFeatureService = new MyFeatureService(); // singleton for app use
```

## Rules

- Use `LoadingMode.Background` for reads, `LoadingMode.Blocking` for writes
- Base URL: `getRuntimeConfig().apiUrl + '/<domain-path>'`
- All types from the project's global types file (`@/types/api`) — never inline type definitions
- Never use `fetch` or Axios directly — always use the project's HTTP client abstraction
