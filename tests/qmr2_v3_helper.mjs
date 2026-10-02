// Test helper: feed a doubt-ledger export to the real quilt-mcp-receipts
// v3 verifier over MCP stdio. Args: rowsFile keyringJson|- mcpClientPath
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const [rowsFile, keyringJson, clientPath] = process.argv.slice(2);
const { McpClient } = await import(pathToFileURL(clientPath).href);
const keyring = keyringJson && keyringJson !== '-' ? JSON.parse(keyringJson) : undefined;
const client = new McpClient({
  qmr2: true,
  v3: true,
  env: { MCP_RECEIPT_SECRET: 'helper-unused-ed25519-only' },
});
await client.handshake();
client.writeLines(fs.readFileSync(rowsFile, 'utf8').split('\n').filter(Boolean));
const args = {};
if (keyring !== undefined) args.keyring = keyring;
const chain = await client.callTool('verify_chain', args);
const attribution = await client.callTool('verify_attribution', args);
console.log(JSON.stringify({ chain: chain.payload, attribution: attribution.payload }));
await client.stop();
