import { SearchPageView } from "@/components/search/SearchPageView";

export default async function SearchPage({
  searchParams
}: {
  searchParams?: Promise<{ query?: string }>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  return <SearchPageView initialQuery={resolvedSearchParams?.query ?? ""} />;
}
