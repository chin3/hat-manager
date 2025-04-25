import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem
} from "@/components/ui/select"

export default function TestComponent() {
  console.log("Injected props:", props);

  // Controlled input state
  const [hatId, setHatId] = useState(props.hat_id || "");
  const [name, setName] = useState(props.name || "");
  const [model, setModel] = useState(props.model || "gpt-3.5");
  const [instructions, setInstructions] = useState(props.instructions || "");
  const [tools, setTools] = useState((props.tools || []).join(', '));
  const [relationships, setRelationships] = useState((props.relationships || []).join(', '));

  // If props change (e.g., after updateElement), sync the state
  useEffect(() => {
    setHatId(props.hat_id || "");
    setName(props.name || "");
    setModel(props.model || "gpt-3.5");
    setInstructions(props.instructions || ""); 9 
    setTools((props.tools || []).join(', '));
    setRelationships((props.relationships || []).join(', '));
  }, [props]); // Re-run when props change

  const handleSave = () => {
    const payload = {
      hat_id: hatId,
      name,
      model,
      instructions,
      tools: tools.split(',').map(t => t.trim()).filter(Boolean),
      relationships: relationships.split(',').map(r => r.trim()).filter(Boolean)
    };

    console.log("Sending updated payload:", payload);

    callAction({ name: "save_hat", payload });

    updateElement({
      name: "TestComponent",
      props: payload
    });
  };

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-semibold">Edit Hat: {hatId}</h3>

      <div>
        <Label htmlFor="name">Name</Label>
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
      </div>

      <div>
        <Label htmlFor="model">Model</Label>
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger id="model" />
          <SelectContent>
            <SelectItem value="gpt-3.5">gpt-3.5</SelectItem>
            <SelectItem value="gpt-4">gpt-4</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="instructions">Instructions</Label>
        <Textarea id="instructions" value={instructions} onChange={(e) => setInstructions(e.target.value)} />
      </div>

      <div>
        <Label htmlFor="tools">Tools (comma-separated)</Label>
        <Input id="tools" value={tools} onChange={(e) => setTools(e.target.value)} />
      </div>

      <div>
        <Label htmlFor="relationships">Relationships (comma-separated)</Label>
        <Input id="relationships" value={relationships} onChange={(e) => setRelationships(e.target.value)} />
      </div>

      <Button className="mt-4 w-full" onClick={handleSave}>
        💾 Save Hat
      </Button>
    </div>
  );
}
