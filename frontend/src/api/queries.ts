import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { postJson, apiFetch } from "./client";
import type {
  CompareResponse,
  EvalRun,
  HealthResponse,
  Mode,
  QueryRequest,
  QueryResponse,
} from "../types/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<HealthResponse>("/health"),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useEvalResults() {
  return useQuery({
    queryKey: ["eval", "results"],
    queryFn: () => apiFetch<EvalRun>("/eval/results"),
    staleTime: 300_000,
  });
}

export function useQueryMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ request, signal }: { request: QueryRequest; signal?: AbortSignal }) =>
      postJson<QueryResponse>("/query", request, signal),
    onSuccess: () => client.invalidateQueries({ queryKey: ["health"] }),
  });
}

export function useCompareMutation() {
  return useMutation({
    mutationFn: ({ question, signal }: { question: string; signal?: AbortSignal }) =>
      postJson<CompareResponse>("/compare", { question }, signal),
  });
}
