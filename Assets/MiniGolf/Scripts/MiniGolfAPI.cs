using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;

[Serializable]
public class InitDataJson  // new helper class for /init endpoint
{
    public int agent_id;
    public int shots;
}

public class MiniGolfAPI : MonoBehaviour
{
    public static string BaseUrl = "http://127.0.0.1:8000"; // Replace with actual API URL

    // 1. Initialize the agent with ID and shots
    public static IEnumerator InitAgent(int agentId, int shots, Action<string> callback)
    {
        string url = $"{BaseUrl}/init";
        // Use the new serializable class instead of an anonymous type
        InitDataJson data = new InitDataJson { agent_id = agentId, shots = shots };
        string jsonData = JsonUtility.ToJson(data);

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();
            HandleResponse(request, callback);
        }
    }

    // 2. Send environment data (walls, nearby objects, hole position, etc.)
    public static IEnumerator SendEnvironmentData(int agentId, Vector3 ballPos, Vector3 holePos, Vector3[] walls, Action<string> callback)
    {
        string url = $"{BaseUrl}/environment";

        // Convert environment data to JSON
        string jsonData = JsonUtility.ToJson(new EnvironmentData(agentId, ballPos, holePos, walls));

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();
            HandleResponse(request, callback);
        }
    }

    // 3. Request a shot decision from the AI
    public static IEnumerator RequestShot(int agentId, Action<ShotData> callback)
    {
        string url = $"{BaseUrl}/shot?agent_id={agentId}";

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                ShotData shot = JsonUtility.FromJson<ShotData>(request.downloadHandler.text);
                callback?.Invoke(shot);
            }
            else
            {
                Debug.LogError($"Shot request failed [{request.responseCode}]: {request.error}");
            }
        }
    }

    // Helper method for error handling
    private static void HandleResponse(UnityWebRequest request, Action<string> callback)
    {
        if (request.result == UnityWebRequest.Result.Success)
        {
            callback?.Invoke(request.downloadHandler.text);
        }
        else
        {
            Debug.LogError($"Request failed [{request.responseCode}]: {request.error}");
            callback?.Invoke(null);
        }
    }

    // Structs for JSON serialization
    [Serializable]
    public class EnvironmentData
    {
        public int agent_id;
        public Vector3 ball_position;
        public Vector3 hole_position;
        public Vector3[] walls;

        public EnvironmentData(int id, Vector3 ball, Vector3 hole, Vector3[] w)
        {
            agent_id = id;
            ball_position = ball;
            hole_position = hole;
            walls = w;
        }
    }

    [Serializable]
    public class ShotData
    {
        public float power;
        public Vector3 direction;
    }
}
