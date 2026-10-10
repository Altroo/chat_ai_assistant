import SvgIcon, { type SvgIconProps } from "@mui/material/SvgIcon";
import type { ReactNode } from "react";

type Props = SvgIconProps & { size?: number };
// Small, local line drawings keep the reference's stroke style without another icon package.
const LineIcon = ({
  size = 24,
  children,
  ...props
}: Props & { children: ReactNode }) => (
  <SvgIcon
    {...props}
    viewBox="0 0 24 24"
    sx={{
      fontSize: size,
      fill: "none",
      stroke: "currentColor",
      strokeWidth: 2,
      strokeLinecap: "round",
      strokeLinejoin: "round",
    }}
  >
    {children}
  </SvgIcon>
);
export const Bot = (props: Props) => (
  <LineIcon {...props}>
    <path d="M12 8V4H8" />
    <rect x="4" y="8" width="16" height="12" rx="2" />
    <path d="M2 14h2m16 0h2M9 13v2m6-2v2" />
  </LineIcon>
);
export const ArrowRight = (props: Props) => (
  <LineIcon {...props}>
    <path d="M5 12h14m-7-7 7 7-7 7" />
  </LineIcon>
);
export const Clock3 = (props: Props) => (
  <LineIcon {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6h4" />
  </LineIcon>
);
export const MessageSquarePlus = (props: Props) => (
  <LineIcon {...props}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10Z M12 7v6m-3-3h6" />
  </LineIcon>
);
export const X = (props: Props) => (
  <LineIcon {...props}>
    <path d="m6 6 12 12M6 18 18 6" />
  </LineIcon>
);
export const Send = (props: Props) => (
  <LineIcon {...props}>
    <path d="m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13" />
  </LineIcon>
);
export const Square = (props: Props) => (
  <LineIcon {...props}>
    <rect x="5" y="5" width="14" height="14" rx="2" />
  </LineIcon>
);
