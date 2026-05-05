import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { UploadForm } from "./_components/upload-form";

interface CategoryRead {
  id: string;
  slug: string;
  display_name: string;
  path: string;
  parent_id: string | null;
  children: CategoryRead[];
}

interface BrandKitRead {
  id: string;
  name: string;
}

export interface LeafCategory {
  id: string;
  display_name: string;
  path: string;
}

function collectLeaves(nodes: CategoryRead[]): LeafCategory[] {
  const leaves: LeafCategory[] = [];
  const walk = (node: CategoryRead) => {
    if (node.children.length === 0) {
      leaves.push({ id: node.id, display_name: node.display_name, path: node.path });
    } else {
      node.children.forEach(walk);
    }
  };
  nodes.forEach(walk);
  return leaves;
}

export default async function NewProductPage() {
  const token = await getToken();

  let leafCategories: LeafCategory[] = [];
  let brandKits: BrandKitRead[] = [];

  try {
    const tree = await apiGet<CategoryRead[]>("/api/v1/categories", token ?? undefined);
    leafCategories = collectLeaves(tree);
  } catch {
    // API may not be reachable locally — form still works, select will be empty
  }

  try {
    brandKits = await apiGet<BrandKitRead[]>("/api/v1/brand-kits", token ?? undefined);
  } catch {
    // Brand kits are optional — form works without them
  }

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-lg font-medium">Add new SKU</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Upload a flatlay or worn-on-mannequin photo
          </p>
        </div>
      </div>
      <UploadForm leafCategories={leafCategories} brandKits={brandKits} token={token} />
    </div>
  );
}
