import { NextRequest, NextResponse } from 'next/server';

// Target base URL for the underlying API services
const TARGET_BASE_URL = 'https://ft-osint-api.duckdns.org/api';

// Simple map matching your specific tool endpoints
const ENDPOINT_MAP: Record<string, string> = {
  adv: 'adv',
  paytm: 'paytm',
  imei: 'imei',
  calltracer: 'calltracer',
  upi: 'upi',
  ifsc: 'ifsc',
  number: 'number',
  pincode: 'pincode',
  ip: 'ip',
  challan: 'challan',
  ff: 'ff',
  bgmi: 'bgmi',
  snap: 'snap',
  email: 'email',
  vehicle: 'vehicle',
  git: 'git',
  insta: 'insta',
  tg: 'tg',
  tgidinfo: 'tgidinfo',
  numleak: 'numleak'
};

export async function GET(
  request: NextRequest,
  { params }: { params: { tool: string } }
) {
  const tool = params.tool;
  const { searchParams } = new URL(request.url);
  
  // Extract custom configuration parameters
  const userKey = searchParams.get('key');
  
  if (!userKey) {
    return NextResponse.json({ error: 'API key is required' }, { status: 401 });
  }

  if (!ENDPOINT_MAP[tool]) {
    return NextResponse.json({ error: 'Requested tool endpoint not found' }, { status: 404 });
  }

  // --- API VALIDATION & LOGGING ENGINE ---
  // In production, fetch/update this records from your database (e.g., Supabase, MongoDB)
  // For Vercel demo/edge validation, we extract configuration from simulated state or headers
  const mockDbKey = {
    key: "shayan_demo_key",
    allowedTools: ["all"], // or specific tools array like ['number', 'upi']
    expiry: new Date("2027-12-31T23:59:59").getTime(),
    limit: 1000,
    used: 142
  };

  // 1. Verify Key Authenticity
  if (userKey !== mockDbKey.key) {
    return NextResponse.json({ error: 'Invalid API Key provided' }, { status: 403 });
  }

  // 2. Verify Expiration Date & Time
  if (Date.now() > mockDbKey.expiry) {
    return NextResponse.json({ error: 'API Key has expired' }, { status: 403 });
  }

  // 3. Verify Request Limits
  if (mockDbKey.used >= mockDbKey.limit) {
    return NextResponse.json({ error: 'Daily/Total request limit reached for this key' }, { status: 429 });
  }

  // 4. Verify Tool Scope Access
  if (!mockDbKey.allowedTools.includes('all') && !mockDbKey.allowedTools.includes(tool)) {
    return NextResponse.json({ error: `This key does not have access to the [${tool}] tool` }, { status: 403 });
  }

  // Gather query parameters passed by the user (excluding our internal management keys)
  const targetParams = new URLSearchParams();
  searchParams.forEach((value, key) => {
    if (key !== 'key') targetParams.append(key, value);
  });

  // Capture the searched value for logging purposes
  const searchValue = targetParams.toString() || 'Empty Query';

  try {
    // Construct target URL and append clean query parameters
    const targetUrl = `${TARGET_BASE_URL}/${ENDPOINT_MAP[tool]}?key=&${targetParams.toString()}`;
    
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'Upstream server error encountered' }, { status: response.status });
    }

    const data = await response.json();

    // Append developer branding cleanly into the JSON response layout
    const brandedResponse = {
      developer: "SHAYAN_EXPLORER",
      status: "success",
      tool_executed: tool,
      query_logged: searchValue,
      timestamp: new Date().toISOString(),
      results: data
    };

    return NextResponse.json(brandedResponse, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
      }
    });

  } catch (error) {
    return NextResponse.json({ error: 'Gateway timeout or internal processing error' }, { status: 500 });
  }
}
