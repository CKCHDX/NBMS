package com.oscyra.sbms.ui;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.oscyra.sbms.R;
import com.oscyra.sbms.data.Contact;

import java.util.ArrayList;

public class ContactAdapter extends ArrayAdapter<Contact> {
    private final Context context;
    private final ArrayList<Contact> contacts;

    public ContactAdapter(@NonNull Context context, @NonNull ArrayList<Contact> contacts) {
        super(context, 0, contacts);
        this.context = context;
        this.contacts = contacts;
    }

    @NonNull
    @Override
    public View getView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        if (convertView == null) {
            convertView = LayoutInflater.from(context).inflate(R.layout.contact_list_item, parent, false);
        }

        Contact contact = contacts.get(position);

        TextView nameView = convertView.findViewById(R.id.contact_name);
        TextView phoneView = convertView.findViewById(R.id.contact_phone);

        nameView.setText(contact.getDisplayName());
        phoneView.setText(contact.getPhoneNumber());

        return convertView;
    }
}
