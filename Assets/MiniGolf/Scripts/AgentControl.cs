using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

/// <summary>
/// Controls the AI golf ball based on API decisions.
/// </summary>
[RequireComponent(typeof(Rigidbody))]
public class AgentControl : MonoBehaviour
{
    public static AgentControl instance;

    [SerializeField] private float MaxForce = 5f;
    [SerializeField] private float stopThreshold = 0.1f; // velocity below which the ball is considered stopped
    [SerializeField] private LayerMask rayLayer; // New: layer mask for raycasting
    private Rigidbody rgBody;
    private bool ballIsStatic = true;
    public int id;
    // New: Each agent will have its own shot count.
    public int shotCount;
    // Flag to ensure single shot request when ball stops
    private bool hasRequestedShot = false;

    public static Vector3 finishPosition;

    [System.Serializable]
    public class WallData {
        public Vector3 hitPoint;
        public float width;
        public float rotation; // Y-axis rotation in degrees
    }

    [System.Serializable]
    public class EnvironmentData
    {
        public int agent_id;
        public Vector3 ball_position;
        public Vector3 hole_position;
        public WallData[] walls; // Changed from Vector3[] to WallData[]
    }

    IEnumerator PostEnvironmentData(EnvironmentData data)
    {
        string jsonData = JsonUtility.ToJson(data);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
        // updated backend url
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:8000/environment", "POST");
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        // {
        //     Debug.Log("Environment data sent successfully: " + request.downloadHandler.text);
        // }
        // else
        {
            Debug.LogError("Error sending environment data: " + request.error);
        }
    }

    private void Awake()
    {
        instance = this; // NEW: Set the static instance so that it can be referenced in static methods.
        rgBody = GetComponent<Rigidbody>();
        shotCount = 5;

        GameObject finishObj = GameObject.FindGameObjectWithTag("Finish");
        if (finishObj != null)
        {
            finishPosition = finishObj.transform.position;
        }
        // Start the coroutine to process shots for this agent
        StartCoroutine(ProcessShots());
    }

    IEnumerator ProcessShots()
    {
        while (shotCount > 0)
        {
            // Wait until the ball is stopped.
            yield return new WaitUntil(() => rgBody.linearVelocity.magnitude < stopThreshold);
            
            shotCount--;
            Debug.Log("[DEBUG] Agent " + id + " has completed " + (5 - shotCount) + " shots.");
            
            // Send shot count update to backend
            StartCoroutine(UpdateShotCount());
            
            // Gather environment info.
            Vector3 currentBallPos = transform.position;
            Vector3 holePos = GameManager.finishPosition; // Adjust as needed.
            WallData[] uniqueWalls = CollectNearbyWallPointsUsingRaycasts();
            // Instead of sending environment data and then requesting a shot,
            // Unity now submits the environment data and awaits the AI's shot decision.
            yield return StartCoroutine(MiniGolfAPI.SubmitEnvironmentData(id, currentBallPos, holePos, uniqueWalls, (shot) =>
            {
                if (shot != null)
                {
                    if (shot.agent_id == id) // only apply shot if decision is for this agent
                    {
                        ApplyShot(shot.power, shot.direction);
                    }
                    else
                    {
                        Debug.Log("Shot assigned to agent " + shot.agent_id + " but current agent id is " + id);
                    }
                }
                else
                {
                    Debug.Log("Shot decision not received for agent " + id);
                }
            }));
            
            // Wait until the ball has started moving.
            yield return new WaitUntil(() => rgBody.linearVelocity.magnitude > stopThreshold);
            // Then wait until it stops again before next shot.
            yield return new WaitUntil(() => rgBody.linearVelocity.magnitude < stopThreshold);
        }
    }

    // Add this method to update the backend shot count
    private IEnumerator UpdateShotCount()
    {
        string url = $"{MiniGolfAPI.BaseUrl}/update_shots";
        string jsonData = JsonUtility.ToJson(new ShotUpdateData { agent_id = id, shots_remaining = shotCount });
        
        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log($"Shot count update sent successfully for agent {id}");
            }
            else
            {
                Debug.LogError($"Error sending shot count update: {request.error}");
            }
        }
    }

    // Add this class for serializing shot update data
    [System.Serializable]
    public class ShotUpdateData
    {
        public int agent_id;
        public int shots_remaining;
    }

    /// <summary>
    /// Applies the AI-calculated shot.
    /// </summary>
    public void ApplyShot(float power, Vector3 direction)
    {
        ballIsStatic = false;
        // Reset the flag so next stop triggers a new request
        hasRequestedShot = false;
        power = Mathf.Clamp(power, 0, MaxForce);

        // Zero out the vertical component to prevent bouncing.
        direction.y = 0;

        // Apply force
        rgBody.AddForce(direction.normalized * power, ForceMode.Impulse);
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.name == "Destroyer")
        {
            // NEW: Call the backend to deduct score for this agent.
            StartCoroutine(MiniGolfAPI.DeductScore(id, (response) =>
            {
                Debug.Log("Deduct score response for agent " + id + ": " + response);
            }));
            // Existing behavior: reposition the agent and halt movement.
            transform.position = new Vector3(0, 0.5f, 0);
            rgBody.linearVelocity = Vector3.zero;
        }
    }

    // NEW: Updated method to collect nearby wall points using raycasts that pass through agents or ball.
    public static WallData[] CollectNearbyWallPointsUsingRaycasts()
    {
        float rayLength = 20f; // Maximum raycast distance
        int rayCount = 360;    // Cast one ray per degree
        HashSet<int> uniqueIDs = new HashSet<int>();
        List<WallData> wallList = new List<WallData>();

        for (int i = 0; i < rayCount; i++)
        {
            float rad = i * Mathf.Deg2Rad;
            Vector3 dir = new Vector3(Mathf.Cos(rad), 0, Mathf.Sin(rad));
            Ray ray = new Ray(AgentControl.instance.transform.position, dir);
            RaycastHit[] hits = Physics.RaycastAll(ray, rayLength, AgentControl.instance.rayLayer);
            if (hits.Length > 0)
            {
                System.Array.Sort(hits, (h1, h2) => h1.distance.CompareTo(h2.distance));
                foreach (RaycastHit hit in hits)
                {
                    if (hit.collider.gameObject == AgentControl.instance.gameObject)
                        continue;
                    if (hit.collider.CompareTag("Agent") || hit.collider.CompareTag("Ball"))
                        continue;
                    int hitID = hit.collider.gameObject.GetInstanceID();
                    if (!uniqueIDs.Contains(hitID))
                    {
                        uniqueIDs.Add(hitID);
                        WallData wd = new WallData();
                        wd.hitPoint = hit.point;
                        wd.width = hit.collider.bounds.size.x;
                        float rotation = hit.collider.transform.eulerAngles.y;
                        rotation = (rotation + 180f) % 360f;
                        if (hit.collider.CompareTag("plus90"))
                        {
                            rotation = (rotation + 90f) % 360f;
                        }
                        wd.rotation = rotation % 180f;
                        wallList.Add(wd);
                    }
                    break; // Only take the first valid hit per ray.
                }
            }
        }
        // Log the collected walls in Unity.
        string wallLog = "Collected walls: ";
        foreach (WallData wall in wallList)
        {
            wallLog += $"[Point: {wall.hitPoint}, Width: {wall.width}, Rotation: {wall.rotation}] ";
        }
        Debug.Log(wallLog);
        // Also log to the backend.
        // AgentControl.instance.StartCoroutine(MiniGolfAPI.LogWalls(wallLog));
        return wallList.ToArray();
    }

    // Updated: method to perform raycast and return the clicked point
    private Vector3 ClickedPoint()
    {
        float sphereRadius = 5f; // adjust as needed
        Collider[] hitColliders = Physics.OverlapSphere(transform.position, sphereRadius, rayLayer, QueryTriggerInteraction.Collide);
        if (hitColliders.Length > 0)
        {
            Vector3 avgPoint = Vector3.zero;
            foreach (Collider hit in hitColliders)
            {
                avgPoint += hit.transform.position;
            }
            avgPoint /= hitColliders.Length;
            return avgPoint;
        }
        else
        {
            return transform.position;
        }
    }

#if UNITY_EDITOR
    private void OnDrawGizmos()
    {
        // Only draw raycast gizmos when playing
        if (!Application.isPlaying) return;
        
        int rayCount = 360;       // One ray per degree
        float rayLength = 20f;    // Maximum distance for the raycast
        for (int i = 0; i < rayCount; i++)
        {
            float rad = i * Mathf.Deg2Rad;
            Vector3 direction = new Vector3(Mathf.Cos(rad), 0, Mathf.Sin(rad));
            // Perform raycast using the assigned layer mask
            if (Physics.Raycast(transform.position, direction, out RaycastHit hit, rayLength, rayLayer))
            {
                Gizmos.color = Color.green;
                Gizmos.DrawLine(transform.position, hit.point);
            }
            else
            {
                Gizmos.color = Color.red;
                Gizmos.DrawLine(transform.position, transform.position + direction * rayLength);
            }
        }
    }
#endif
}