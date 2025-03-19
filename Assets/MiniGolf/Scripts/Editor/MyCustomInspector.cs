using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(MonoBehaviour), true)]
public class MyCustomInspector : Editor
{
    private GUIStyle myStyle;
    
    public override void OnInspectorGUI()
    {
        // Initialize myStyle in OnGUI so a current skin is available.
        if (myStyle == null)
        {
            myStyle = new GUIStyle(GUI.skin.label);
            myStyle.normal.textColor = Color.white;
        }
        
        GUILayout.Label("Custom Inspector", myStyle);
        DrawDefaultInspector();
    }
}