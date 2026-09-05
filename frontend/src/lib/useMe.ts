import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./api";

export interface Me {
  account_id: number;
  username: string;
  role: "seller" | "operator";
  shop_id: number | null;
  shop_name: string | null;
  acting_as_shop_id: number | null;
  acting_as_shop_name: string | null;
}

export function useMe() {
  return useQuery<Me>({
    queryKey: ["me"],
    queryFn: () => apiFetch<Me>("/me"),
    retry: false,
  });
}
