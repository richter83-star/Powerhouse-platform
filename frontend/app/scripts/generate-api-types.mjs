import { execFileSync } from 'child_process';
import path from 'path';

const input = process.env.OPENAPI_SCHEMA || 'http://localhost:8001/openapi.json';
const output = process.env.OPENAPI_OUTPUT || 'lib/api-types.ts';
const binName = process.platform === 'win32' ? 'openapi-typescript.cmd' : 'openapi-typescript';
const binPath = path.join(process.cwd(), 'node_modules', '.bin', binName);

execFileSync(binPath, [input, '-o', output], { stdio: 'inherit', shell: true });
