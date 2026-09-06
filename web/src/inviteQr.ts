import QRCode from "qrcode";

export function inviteRegisterPath(companyCode: string): string {
  return `/register?company_code=${encodeURIComponent(companyCode)}`;
}

export function inviteRegisterUrl(companyCode: string): string {
  return `${window.location.origin}${inviteRegisterPath(companyCode)}`;
}

export function inviteQrDataUrl(companyCode: string): Promise<string> {
  return QRCode.toDataURL(inviteRegisterUrl(companyCode), { width: 192, margin: 1 });
}
